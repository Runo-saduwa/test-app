from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAI
from typing import List, Dict, Optional
from enum import Enum
import asyncio
import json
import os
import tempfile
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Cowabunga AI",
    description="Democratizing Software Quality Assurance through AI",
    version="1.0.0",
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class StepType(str, Enum):
    NAVIGATION = "navigation"
    INPUT = "input"
    CLICK = "click"
    ASSERTION = "assertion"
    CUSTOM = "custom"

class AuthCredentials(BaseModel):
    email: str
    password: str

class TestData(BaseModel):
    auth_credentials: Optional[AuthCredentials] = None
    form_data: Optional[Dict[str, str]] = None
    custom_data: Optional[Dict] = None

class Step(BaseModel):
    step_id: str
    order: int
    name: str
    description: str
    step_type: StepType
    automation_code_headless: str
    automation_code_headed: str
    expected_result: str
    acceptance_criteria_covered: List[str] = Field(default_factory=list)

class TestCase(BaseModel):
    test_case_id: str
    name: str
    description: str
    steps: List[Step]
    acceptance_criteria_covered: List[str] = Field(default_factory=list)

class FeatureTestResponse(BaseModel):
    feature_name: str
    test_cases: List[TestCase]

class FeatureInput(BaseModel):
    url: str
    feature_name: str
    feature_description: str
    acceptance_criteria: List[str]
    test_data: Optional[TestData] = None
    headless: bool = True

class StepResult(BaseModel):
    step_id: str
    name: str
    status: str
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    execution_time: float
    acceptance_criteria_covered: List[str] = Field(default_factory=list)

class TestResult(BaseModel):
    test_case_id: str
    name: str
    status: str
    steps_results: List[StepResult]
    acceptance_criteria_covered: List[str] = Field(default_factory=list)
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration: Optional[float] = None

@app.post("/api/v1/generate-feature-test", response_model=FeatureTestResponse)
async def generate_feature_test(feature_input: FeatureInput):
    prompt = f"""
    Generate detailed test cases for the following feature:
    URL: {feature_input.url}
    Feature Name: {feature_input.feature_name}
    Description: {feature_input.feature_description}
    
    Acceptance Criteria:
    {chr(10).join(f'- {ac}' for ac in feature_input.acceptance_criteria)}
    
    Test Data:
    {json.dumps(feature_input.test_data.dict() if feature_input.test_data else {}, indent=2)}
    
    Mode: {"Headless" if feature_input.headless else "Headed Chrome"}
    
    Create a complete test suite with detailed steps. For each step, provide:
    1. Step name and description
    2. Step type (navigation/input/click/assertion)
    3. Playwright code for both headless and headed execution
    4. Expected results
    5. Which acceptance criteria each step verifies
    
    Return the response in FeatureTestResponse format with proper test cases and steps.
    """
    
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a QA automation expert specialized in Playwright testing. Generate precise, runnable test code."
                },
                {"role": "user", "content": prompt}
            ],
            response_format=FeatureTestResponse
        )
        
        return completion.choices[0].message.parsed
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate test case: {str(e)}"
        )

@app.post("/api/v1/execute-test", response_model=TestResult)
async def execute_test(test_case: TestCase, headless: bool = True):
    # Create a temporary Python file with the complete test script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
import asyncio
from playwright.async_api import async_playwright
import json

async def run_test():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=%s)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
""" % str(headless))

        # Add each step's code with proper error handling and timing
        for step in test_case.steps:
            code = step.automation_code_headless if headless else step.automation_code_headed
            # Remove any browser launch code from individual steps
            code = code.replace("const browser = await chromium.launch({ headless: false });", "")
            code = code.replace("const context = await browser.newContext();", "")
            code = code.replace("const page = await context.newPage();", "")
            
            f.write(f"""
            # {step.name}
            try:
                step_start = asyncio.get_event_loop().time()
                {code}
                step_end = asyncio.get_event_loop().time()
                print(json.dumps({{
                    "step_id": "{step.step_id}",
                    "name": "{step.name}",
                    "status": "passed",
                    "execution_time": step_end - step_start
                }}))
            except Exception as e:
                step_end = asyncio.get_event_loop().time()
                print(json.dumps({{
                    "step_id": "{step.step_id}",
                    "name": "{step.name}",
                    "status": "failed",
                    "error": str(e),
                    "execution_time": step_end - step_start
                }}))
                raise
""")

        f.write("""
        finally:
            await context.close()
            await browser.close()

asyncio.run(run_test())
""")
        
        f.flush()
        script_path = f.name

    results = []
    start_time = datetime.utcnow()
    
    try:
        # Execute the test script
        process = await asyncio.create_subprocess_exec(
            'python3', script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # Process results
        output_lines = stdout.decode().strip().split('\n')
        for line in output_lines:
            if line.strip():
                try:
                    step_result = json.loads(line)
                    results.append(StepResult(
                        step_id=step_result["step_id"],
                        name=step_result["name"],
                        status=step_result["status"],
                        error_message=step_result.get("error"),
                        execution_time=step_result["execution_time"],
                        acceptance_criteria_covered=[]
                    ))
                except json.JSONDecodeError:
                    continue

        end_time = datetime.utcnow()
        overall_status = "passed" if all(r.status == "passed" for r in results) else "failed"
        
        return TestResult(
            test_case_id=test_case.test_case_id,
            name=test_case.name,
            status=overall_status,
            steps_results=results,
            acceptance_criteria_covered=test_case.acceptance_criteria_covered,
            start_time=start_time,
            end_time=end_time,
            total_duration=(end_time - start_time).total_seconds()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        os.unlink(script_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)