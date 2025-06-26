import re,os,time,json,random,subprocess,ollama,argparse,pandas as pd
from glob import glob
from tqdm import tqdm
from openai import OpenAI
import settings
import uuid

from settings import home_path,response_title,response_folder_path,targetOS,dir_ttp,dict_ttp,csv_ttp,csv_ttp_noPr,dir_cti,generate_secure_random_string,loadSettings,saveRecord,file_encoding
empty_char=""
"""
Data lookup
"""
def dataLookUp(ID:str="N",type:str="enterprise"):
    data=""
    if ID[0]=="T":
        if ID[1]=="A":
            data="tactics.json"
        else:
            data="techniques_detailed.json"
    elif ID[0]=="S":data="softwares.json"
    elif ID[0]=="G":data="groups.json"
    elif ID[0]=="C":data="campaigns.json"
    elif ID[0]=="A":data="assets.json"
    elif ID[0]=="D":data="datasources.json"
    else: return "Can't find result"

    with open(os.path.join(os.getcwd(),"data",data),"r")as file:
        content=json.load(file)
    
    if ID[0]=="T":return {"ID":content[type][ID]["ID"],
                          "name":content[type][ID]["name"],
                          "description":content[type][ID]["description"]}
    else:return {"ID":content[ID]["ID"],
                "name:":content[ID]["name"],
                "description:":content[ID]["description"]}
"""
Code extraction
"""
def extract_header_and_source_SingleAction(responseFolderPath: str,responseContent:str):
    responseDict={}

    # Get output filenames
    action = re.findall(r'- Action: "(.*?)"\n', responseContent)[0]
    headerFilename = re.findall(r'- Header filename: "(.*?)"\n', responseContent)[0].split(".")[0]
    cppFilename = re.findall(r'- C\+\+ source filename: "(.*?)"\n', responseContent)[0].split(".")[0]
    
    # Get header file content
    headerPattern = re.compile(r'<header>\n```cpp\n(.*?)\n```\n</header>', re.DOTALL)
    headerContent = headerPattern.findall(responseContent)[0]
        
    # Get cpp file content
    cppPattern = re.compile(r'<cppfile>\n```cpp\n(.*?)\n```\n</cppfile>', re.DOTALL)
    cppContent = cppPattern.findall(responseContent)[0]

    # print(f'\t- Header {fileNum + 1}:\t{headerFilename}')
    # print(f'\t- C++ code {fileNum + 1}:\t{cppFilename}')
        
    responseDict["action"][headerFilename] = action
    responseDict["header"][headerFilename] = headerContent
    responseDict["cpp"][headerFilename]    = cppContent

    # Write header file
    path_headerFile=os.path.join(responseFolderPath,"code",headerFilename+".h")
    with open(path_headerFile, 'w', encoding = file_encoding) as header:
        header.write(headerContent)
        
    # Write cpp file
    path_cppFile=os.path.join(responseFolderPath,"code",cppFilename+".cpp")
    with open(path_cppFile, 'w', encoding = file_encoding) as cpp:
        cpp.write(cppContent)
    return responseDict

def extract_header_and_source(responseFolderPath: str,code_of_action:list):
    print("[+]Start Extracting header and source")
    if not os.path.exists(os.path.join(responseFolderPath,"code")):
        os.makedirs(os.path.join(responseFolderPath,"code"))
    
    
    responseDict = {
        "action": {},
        "header": {},
        "cpp": {}
    }
    
    print(f"[+] Extracting code. Codes will be exported in \\{response_title}\\code")
    for fileNum, responseFile in enumerate(code_of_action):
        if "main" in responseFile:
            continue
        responseContent=code_of_action[fileNum]

        # Get output filenames
        action = re.findall(r'- Action: "(.*?)"\n', responseContent)[0]
        headerFilename = re.findall(r'- Header filename: "(.*?)"\n', responseContent)[0].split(".")[0]
        cppFilename = re.findall(r'- C\+\+ source filename: "(.*?)"\n', responseContent)[0].split(".")[0]

        # Check filenames
        if headerFilename != cppFilename:
            continue
        
        # Get header file content
        headerPattern = re.compile(r'<header>\n```cpp\n(.*?)\n```\n</header>', re.DOTALL)
        headerContent = headerPattern.findall(responseContent)[0]
        
        # Get cpp file content
        cppPattern = re.compile(r'<cppfile>\n```cpp\n(.*?)\n```\n</cppfile>', re.DOTALL)
        cppContent = cppPattern.findall(responseContent)[0]

        print(f'\t- Action {fileNum + 1}:\t{action}')
        # print(f'\t- Header {fileNum + 1}:\t{headerFilename}')
        # print(f'\t- C++ code {fileNum + 1}:\t{cppFilename}')
        
        responseDict["action"][headerFilename] = action
        responseDict["header"][headerFilename] = headerContent
        responseDict["cpp"][headerFilename]    = cppContent

        # Write header file
        path_headerFile=os.path.join(responseFolderPath,"code",headerFilename+".h")
        with open(path_headerFile, 'w', encoding = file_encoding) as header:
            header.write(headerContent)
        
        # Write cpp file
        path_cppFile=os.path.join(responseFolderPath,"code",cppFilename+".cpp")
        with open(path_cppFile, 'w', encoding = file_encoding) as cpp:
            cpp.write(cppContent)

    print("[-]Finish Extracting header and source") 
    return responseDict
     
def extract_main(responseContent: str,responseFolderPath: str):
    mainText = responseContent

    mainCode = mainText.split("```cpp")[-1].split("\n```")[0]

    with open(f'{responseFolderPath}\\code\\main.cpp', 'w', encoding = file_encoding) as mainCpp:
        mainCpp.write(mainCode)
        
    return mainCode

def extract_from_debug(debug_result:str,codeOutputPath: str,jsonContent:dict):
    fileContents = debug_result.split("------------------------------------------------\n")
    
    for file in fileContents:
        if re.findall(r'- Content changed: Yes', file):
            filename = re.findall(r'- Filename: (.*?)\n', file)[0]
            codeName = filename.split(".")[0]
            fileCode = file.split("cpp```\n")[-1].split("\n```")[0]
            jsonContent["cpp"][codeName] = fileCode
            
            with open(os.path.join(codeOutputPath,filename), mode = 'w', encoding = file_encoding) as fileCodeOutput:
                fileCodeOutput.write(fileCode)
            
    return jsonContent
"""
Code of action generation
"""
def codeofActionGeneration(codeActionList: list):
    print("[+]Start  generating functions")
    List_codeofAction_generation=[]
    with tqdm(total = len(codeActionList), ncols = 100, desc = "Code Generation") as pbar: 
        for actionNum, action in enumerate(codeActionList):
            systemPrompt = textLoader("SystemPrompt_CodeofAction")
            taskPrompt = textLoader("UserPompt_CodeofActionGeneration_SingleAction")+"<action>"+action+"</action>"
            messages = [
                {"role": "system", "content": systemPrompt},
                {"role": "user", "content": taskPrompt}
            ]
            response = Llmrequest(messages)
            List_codeofAction_generation.append(response)
            #extract_header_and_source_SingleAction
            pbar.update()
    return List_codeofAction_generation

def codeofActionGeneration_SingleAction(action:str):
    systemPrompt = textLoader("SystemPrompt_CodeofActionGeneration_SingleAction")
    taskPrompt = textLoader("UserPompt_CodeofActionGeneration_SingleAction")
    messages = [
                {"role": "system", "content": systemPrompt},
                {"role": "user", "content": taskPrompt}
            ]
        
    response = Llmrequest(messages=messages)
    print("[-]Finish generating functions")   
    return response
"""
Code Review
"""
def action_review_prompting(actionDict: dict):
    messageList = []
    
    actionCodeReviewSystemPrompt = textLoader(txtName=f"SystemPrompt_CodeofActionReview")
    
    for filename in actionDict["header"].keys():
        action = actionDict["action"][filename]
        header = actionDict["header"][filename]
        code = actionDict["cpp"][filename]

        actionCodeReviewTaskPrompt = f'''
        <header>
        {header}
        </header>
        <code>
        {code}
        </code>
        <task>
        {action}
        </task>
        '''
        
        message = [
            {"role": "system", "content": actionCodeReviewSystemPrompt},
            {"role": "user", "content": actionCodeReviewTaskPrompt}
        ]
        
        messageList.append([filename, message])
    
    return messageList

def action_code_review(infoOfHeaderAndSource:dict):
    # Read action code file
    Json_code_review={}
    jsonContent = infoOfHeaderAndSource
    messageList = action_review_prompting(jsonContent)

    # Get code review responses
    with tqdm(total=len(messageList), ncols=100, desc="Code Review") as pbar:
        for message in messageList:
            response = Llmrequest(message[1])
            Json_code_review[message[0]]=f'- Filename: "{message[0]}"\n'+response
            
            pbar.update()
    return Json_code_review

def action_code_review_check(previous_:dict,check_list:dict, codeOutputPath: str):
    actionCodeReviewPass = True
    #這邊是載入的Review紀錄
    Checking={}
    CheckListNextIter={"action":{},"header":{},"cpp":{}}
    for actionCodeReview in check_list:
        taskPass = False
        syntaxPass = False
        headerChanged = False
        sourceChanged = False
        codeReviewContent=check_list[actionCodeReview]
        filename = re.findall(r'- Filename: "(.*?)"\n', codeReviewContent)[0]
        print(f'\t- File: {filename}')
        
        # Check task,syntax error,header change,source file change
        taskPass = bool(re.search(r'- The code completes the task: Yes', codeReviewContent))
        syntaxPass = bool(re.search(r'- Syntax error exists: No', codeReviewContent))
        headerChanged = not bool(re.search(r'- Header file content changed: No', codeReviewContent))
        sourceChanged = not bool(re.search(r'- Source file content changed: No', codeReviewContent))        
        print(f"\t- Task review\t Pass:{taskPass}")
        print(f"\t- Syntax review Pass:{syntaxPass}")
        print(f"\t- Header\t changed:{headerChanged}")
        print(f"\t- Source\t changed:{sourceChanged}")
        print("----------"*3)
        Checking[actionCodeReview]={
            "taskPass" : taskPass,
            "syntaxPass" : syntaxPass,
            "headerChanged" : headerChanged,
            "sourceChanged" : sourceChanged,
        }
        
        # Replace code
        if (not syntaxPass):
            actionCodeReviewPass = False
            print("headerChanged:",headerChanged)
            print("sourceChanged:",sourceChanged)
            CheckListNextIter["action"][filename]=previous_["action"][filename]
            if headerChanged:#filename.h有變就重新寫一次filename.h
                CodeOfHeader = codeReviewContent.split("- Header file content:\n```cpp\n")[-1].split("\n```")[0]
                CheckListNextIter["header"][filename]=CodeOfHeader
                with open(os.path.join(codeOutputPath,f'{filename}.h'), 'w', encoding = file_encoding) as headerCpp:
                    headerCpp.write(CodeOfHeader)
                print(CodeOfHeader==previous_["header"][filename])
            else:CheckListNextIter["header"][filename]=previous_["header"][filename]
            
            if sourceChanged:#filename.cpp有變就重新寫一次filename.cpp
                CodeOfCpp = codeReviewContent.split("- Source file content:\n```cpp\n")[-1].split("\n```")[0]
                CheckListNextIter["cpp"][filename]=CodeOfCpp
                with open(os.path.join(codeOutputPath,f'{filename}.cpp'), 'w', encoding = file_encoding) as sourceCpp:
                    sourceCpp.write(CodeOfCpp)
                print(CodeOfCpp==previous_["cpp"][filename])    
            else:CheckListNextIter["cpp"][filename]=previous_["cpp"][filename]
            
    
    return actionCodeReviewPass,Checking,CheckListNextIter,

def main_code_review(jsonContent:dict,mainCode:str):
    mainCodeReviewSystemPrompt = textLoader(txtName=f"SystemPrompt_MainCodeReview")
    Str_main_code_review=""
    codeStr = ""
    procedureStr = ""
    
    # Code
    for file_num, filename in enumerate(jsonContent["header"].keys()):
        header = jsonContent["header"][filename]
        code = jsonContent["cpp"][filename]
        
        codeStr += f'''<header_{file_num+1}>
{header}
</header_{file_num+1}>
<code_{file_num+1}>
{code}
</code_{file_num+1}>
        '''
    
    # Procedure
    for action in jsonContent["action"].keys():
        procedureStr += jsonContent["action"][action]
        procedureStr += " "
       
    mainCodeReviewTaskPrompt = f'''
{codeStr}
<main.cpp>
{mainCode}
</main.cpp>
<procedure>
{procedureStr}
</procedure>
    '''
    
    message = [
        {"role": "system", "content": mainCodeReviewSystemPrompt},
        {"role": "user", "content": mainCodeReviewTaskPrompt}
    ]
    
    print("[+] Main code review")
    response = Llmrequest(message)

    Str_main_code_review=f'- Filename: "main"\n'+response
    return Str_main_code_review

def main_code_review_check(codeOutputPath: str,Review_of_main_code:str):
    mainCodeReviewPass = True
    mainCodeReviewContent = Review_of_main_code
    taskPass = False
    syntaxPass = False
    

    taskPass = bool(re.search(r'- The project completes the task: Yes', mainCodeReviewContent))
    syntaxPass = bool(re.search(r'- Syntax error exists: No', mainCodeReviewContent))
    contentUnchanged = bool(re.search(r'- Main.cpp file content changed: No', mainCodeReviewContent))
    print(f"\t- Task review:\t {'Pass.' if taskPass else 'Failed.'}")
    print(f"\t- Syntax review:\t {'Pass.' if syntaxPass else 'Failed.'}")
    print(f"\t- Content:\t {'Unchanged' if contentUnchanged else 'Changed'}")
    MainChecking={
        "taskPass":taskPass,
        "syntaxPass":syntaxPass}

    if(not syntaxPass):
        mainCodeReviewPass = False
        if not contentUnchanged:
            print("\t- Header:\t Changed")
            newMainCode = mainCodeReviewContent.split("- Main.cpp file content:\n")[-1].split("```cpp")[-1].split("\n```")[0]
            with open(os.path.join(codeOutputPath,"main.cpp"), 'w', encoding = file_encoding) as mainCpp:
                mainCpp.write(newMainCode)
    else:newMainCode=""#避免空值錯誤
    return mainCodeReviewPass,MainChecking,newMainCode
"""
Code debug
"""
def code_debug_prompting(actionDict: dict, errorMessage: str):
    codeDebugSystemPrompt = textLoader("SystemPrompt_CodeDebug")
    codeDebugTaskPrompt = textLoader("UserPromp_CodeDebug")
    
    for filename in actionDict["header"].keys():
        code = actionDict["cpp"][filename]
        
        codeDebugTaskPrompt += f'''<{filename}.cpp>
{code}
</{filename}.cpp>
'''
    
    codeDebugTaskPrompt += f'''<main.cpp>
{actionDict["main"]}
</main.cpp>
<error_message>
{errorMessage}
</error_message>'''
    
    message = [
        {"role": "system", "content": codeDebugSystemPrompt},
        {"role": "user", "content": codeDebugTaskPrompt}
    ]
    
    return message

def code_debug(errorFilePath: str,jsonContent:dict):
    print(f"[+] Debugging")
    
    # Read compile error message
    with open(errorFilePath, mode = 'r', encoding='utf-16-le') as errorFile:
        errorContent = errorFile.read()
    # Extract error message
    errorMSG = errorContent.split("Copyright (C) Microsoft Corporation.  All rights reserved.\n\n")[-1]
    message = code_debug_prompting(actionDict=jsonContent,errorMessage=errorMSG)
    response = Llmrequest(message)
    return response
"""
Generatemain function
"""
def generate_main_task_template(num: str, header_content: str, cpp_content: str):
    mainTaskPrompt = f'''
<header_{num}>
{header_content}
</header_{num}>
<cpp_{num}>
{cpp_content}
</cpp_{num}>\n'''
    
    return mainTaskPrompt

def generate_main(jsonContent:dict, responseFolderPath: str, codeActionList: list):
    print("[+] Generating main function.")
    
    mainSystemPrompt = r'''Some header files, corresponding C++ source codes, and a list of program procedures will be provided.
Please write a main.cpp program with only main function to rearrange the order and combine all C++ source files according to the procedure list.
Only use functions in the source file, do not implement functions in the main.cpp file.
The response should be in the following format and only contains C++ code:
```cpp
[code]
```
'''
    
    mainTaskPrompt = r''''''
    
    codeList = jsonContent["header"].keys()
    # Add header and source code content
    for codeNum, codeName in enumerate(codeList):
        mainTaskPrompt += generate_main_task_template(codeNum+1, jsonContent["header"][codeName], jsonContent["cpp"][codeName])

    # Add procedure list
    mainTaskPrompt += '<procedure>\n'
    for actionNum, action in enumerate(codeActionList):
        mainTaskPrompt += f'{actionNum+1}. {action}\n'
    mainTaskPrompt += '<\procedure>'
    
    messages = [
        {"role": "system", "content": mainSystemPrompt},
        {"role": "user", "content": mainTaskPrompt}
    ]

    mainMSG = Llmrequest(messages)

    #with open(f'{responseFolderPath}\\{responseTitle}_main.txt', 'w', encoding = file_encoding) as mainResponseFile:
        #mainResponseFile.write(mainMSG)
        
    mainCode = extract_main(mainMSG,responseFolderPath)

    print("\t- Completed")
    
    return mainCode
"""
funtion: request LLM
"""
def Llmrequest(messages:list=[{"role":"user","content":"nothing to say"}],source:str=settings.source,llm:str=settings.llm):
    """ 
    目前有Openai api與Ollama 套件作為LLM來源
    """
        
    def gpt_request(llm:str="gpt-4o-mini",messages: list=[{"role":"user","content":"nothing to say"}]):
        # Get Response from GPT
        api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key = api_key)
        response = client.chat.completions.create(
        model = llm,
        messages = messages,
        temperature = 0
        )
        return response.choices[0].message.content
    def ollama_request(llm:str = "llama3.2", messages:list = [{"role":"user","content":"nothing to say"}]):
        response= ollama.chat(
        model=llm,
        messages=messages
        )
        return response['message']['content']
    if source == "openai":
        return gpt_request(llm=llm,messages=messages)
    elif source == "ollama" :
        return ollama_request(llm=llm,messages=messages)
"""
fuction : compile
"""
def compile_run(responseFolderPath: str,title:str):
    print("\n\n[+] Compiling executable")
    all_cpp_filelist = glob(f"{responseFolderPath}\\code\\*.cpp")
    # Create code review directory
    if not os.path.exists(os.path.join(responseFolderPath,"code","compile_output")):
        os.makedirs(os.path.join(responseFolderPath,"code","compile_output"))

    # Write Powershell Script
    with open(os.path.join(responseFolderPath,"vs_compile.ps1"), mode = 'w', encoding = file_encoding) as vs_script:
        vs_script.write("& 'C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\Common7\\Tools\\Launch-VsDevShell.ps1'\n")
        vs_script.write(f"cd '{responseFolderPath}\\code'\n")
        vs_script.write(f'cl /std:c++17 /EHsc ')
        
        for file in all_cpp_filelist:
            filename = file.split("\\")[-1]
            vs_script.write(f'{filename} ')
        
        vs_script.write(f'/link /OUT:program{title}.exe > compile_output\\{title}_output.txt 2>&1\n')

    # Run Script
    subprocess.run(["powershell", "-File", f'{responseFolderPath}\\vs_compile.ps1'])
    return
"""
fuction : Load the prompt from thedirectory :Prompt:
"""
def textLoader(txtName:str):
    with open(os.path.join(os.getcwd(),"prompt",txtName+".txt"),"r",encoding="utf-8")as file:
        prompt=file.read()
    return prompt
"""
function :generate sigma rule
"""
def sigmaruleGeneration(dict_input:dict={},display:bool=False):
    print("[+]Start generating sigma rule.")
    """
    """
    SystemtPrompt=textLoader(txtName=f"SystemPrompt_sigmaRuleGeneration")
    UserPrompt="<text>"+str(dict_input)+"</text>"
    messages = [
        {"role": "system", "content": SystemtPrompt},
        {"role": "user", "content": UserPrompt}
    ]
    if display:print(messages)
    sigmarule=Llmrequest(messages)
    print("[-]Finish generating sigma rule.")
    return sigmarule
"""
function    :translate Sigma rule to KQL
"""
def KQLGeneration(input:str="",display:bool=False):
    print("[+]Start generating sigma rule.")
    """
    """
    SystemtPrompt=textLoader(txtName=f"SystemPrompt_KQLGeneration")
    UserPrompt="<text>"+input+"</text>"
    messages = [
        {"role": "system", "content": SystemtPrompt},
        {"role": "user", "content": UserPrompt}
    ]
    if display:print(messages)
    KQL=Llmrequest(messages)
    print("[-]Finish generating sigma rule.")
    return KQL
"""
function :generate action list
"""
def generationActionList(dict_input:dict={"inputType":"t2m"},display:bool=False):
    print("[+]Start generating task.")
    """
    type:
        technique,  某個技術的描述(t2m)#default
        tactic      某個戰術的描述(Tt2m)
        software,   某個軟體的描述(s2m)
        group,      某個攻擊者團體的描述(g2m)
        campaign,   某個攻擊事件的描述(c2m)
    """
    if dict_input.__contains__("inputType"):inputType= dict_input['inputType']

    systemt_prompt_generationActionList=textLoader(txtName=f"SystemPrompt_actionListGeneration")
    user_prompt_generationActionList="<given text>"+str(dict_input)+"</text>"
    messages = [
        {"role": "system", "content": systemt_prompt_generationActionList},
        {"role": "user", "content": user_prompt_generationActionList}
    ]
    if display:print(messages)
    attack_script=Llmrequest(messages)
    
    
    attackplan = re.findall(r'<attackplan>(.*?)</attackplan>', attack_script)
    actions = re.findall(r'<action>(.*?)</action>', attack_script)
    print("[-]Finish generating task.")
    return attackplan,actions
"""

code :workflow of the automated generation malware written in C++
以dictionary作為輸入
需要指定進行的任務為生成惡意程式或是只生成任務列表

    inputType:
        software,   某個軟體的描述(s2m)
        group,      某個攻擊者團體的描述(g2m)
        campaign,   某個攻擊事件的描述(c2m)
        technique,  某個技術的描述(t2m)
        tactic      某個戰術的描述(Tt2m)
    operation:
        1 僅生成action list(攻擊計畫)
        2 生成action list(攻擊計畫)之後繼續生成程式碼
        3 生成action list與程式碼之後編譯出最終的惡意軟體
"""
def workflow(
    dictInput:dict={'inputType':"t2m"},
    operation:int=1):
    ID=dictInput['ID']
    filename=f"{ID}_"+generate_secure_random_string(10)
    filename_jsonRecord=f"Log_{filename}.json"
    loadSettings()
    JsonRecord=settings.JsonRecord
    JsonRecord["Input"]=dictInput
    
    workflow_folder_path    = os.path.join(response_folder_path,f"{filename}")
    code_json_file_path     = os.path.join(response_folder_path,f"{filename}",f"{response_title}.json")
    code_output_path        = os.path.join(workflow_folder_path,"code")
    os.makedirs(workflow_folder_path)
    os.makedirs(code_output_path)
    # Initialization
    #loadSettings()
    #Step.1    #Generate Action list from cti reports or examples of ttps
    #Step.2    # Generate code from action in action list
    #Step.2.1    # Generating code by OPENAI's api
    #Step.2.2    # Extract information from the response 
    if operation<4:
        try:
            # 生成action list
            saveRecord(filename_jsonRecord,path=workflow_folder_path)
            JsonRecord["Attack plan"],JsonRecord["Action list"]=generationActionList(dictInput)
            saveRecord(filename_jsonRecord,path=workflow_folder_path)
            JsonRecord["Code of Action"] = codeofActionGeneration(codeActionList=JsonRecord["Action list"])
            saveRecord(filename_jsonRecord,path=workflow_folder_path)
            
            # 根據action list生成每個action 的code
            # 擷取code生成 .cpp檔案
            JsonRecord["Code review"]={}
            JsonRecord["Code review"].update(extract_header_and_source(responseFolderPath=workflow_folder_path,code_of_action=JsonRecord["Code of Action"]))
            saveRecord(filename_jsonRecord,path=workflow_folder_path)  
        except Exception as e:
            print(f'{e}\n')
            return 
    
    #Step.3    # Code combination
    #Step.3.1   # Action code review
    #Loop in 3.1    # Repeat code review if the code did not fit the purpose
    try:
        code_review_iter = 0
        code_review_passed = False

        while not code_review_passed and code_review_iter < 2:
            #這邊對當前的code進行review
            JsonRecord["Code review"]["Record"]=action_code_review(infoOfHeaderAndSource=JsonRecord["Code review"])
            saveRecord(filename_jsonRecord,path=workflow_folder_path)
            
            
            code_review_passed,JsonRecord["Code review"]["Checking"] ,new_= action_code_review_check(previous_=JsonRecord["Code review"],check_list=JsonRecord["Code review"]["Record"],codeOutputPath=code_output_path)
            saveRecord(filename_jsonRecord,path=workflow_folder_path)
            if not code_review_passed:
                print("Results of Review Checking:")
                code_review_iter+=1
                JsonRecord["Code review"]={}
                JsonRecord["Code review"].update(new_)
        
        saveRecord(filename_jsonRecord,path=workflow_folder_path)
        
        
        
        jsonContent={"action":{},"cpp":{},"header":{},"main":{}}
        jsonContent["action"].update(JsonRecord["Code review"]["action"])
        jsonContent["cpp"].update(JsonRecord["Code review"]["cpp"])
        jsonContent["header"].update(JsonRecord["Code review"]["header"])
        #Step.3.2   # Generate main function(This step will be executed after review is done.)
        main_code = generate_main(jsonContent=jsonContent,responseFolderPath=workflow_folder_path,codeActionList=JsonRecord["Action list"])
        JsonRecord["Main code review"]={"Code":main_code}
        saveRecord(filename_jsonRecord,path=workflow_folder_path)
        
        #Step.3.3   # Review main function
        main_code_review_passed = False
        main_code_review_iter=0
        while not main_code_review_passed and main_code_review_iter < 2:
            #
            Review_of_main_code=main_code_review(jsonContent=JsonRecord["Code review"],mainCode=main_code)
            JsonRecord["Main code review"].update({"Review":Review_of_main_code})
            saveRecord(filename_jsonRecord,path=workflow_folder_path)
            
            #
            main_code_review_passed,MainCodeReviewCheck,NewMainCode = main_code_review_check(codeOutputPath=code_output_path,Review_of_main_code=Review_of_main_code)
            JsonRecord["Main code review"].update({"Record":MainCodeReviewCheck})
            
            #
            if not main_code_review_passed:
                main_code_review_iter+=1
                JsonRecord["Main code review"]={"Code":NewMainCode}
        
        #Step.3.4    # Compile executable
        #Loop of 3.4
        jsonContent["main"]=JsonRecord["Main code review"]["Code"]
        compile_num = 0
        compile_success = False
        while not compile_success and compile_num <3:
            compile_run(responseFolderPath=workflow_folder_path,title=f"{filename}")
            
            debug_count=0
            ## Compile success.
            if os.path.exists(os.path.join(workflow_folder_path,"code",f"program{filename}.exe")):
                compile_success = True
                print(f"\t- Compile {compile_num} success")
            else:
                compile_success = False
                debug_count+=1
                if debug_count>5:break
                print(f"\t- Compile {compile_num} failed")
                errorFilePath=f'{workflow_folder_path}\\code\\compile_output\\{filename}_output.txt'
                debug_result = code_debug(errorFilePath=errorFilePath,jsonContent=jsonContent)
                JsonRecord["Debug"]={"Record":debug_result}
                saveRecord(filename_jsonRecord,path=workflow_folder_path)
                json_fixed=extract_from_debug(debug_result=debug_result,codeOutputPath=code_output_path,jsonContent=jsonContent)
                jsonContent.update(json_fixed)
                JsonRecord["Debug"]["Checking"]=json_fixed
                print(f"\t- Debug complete")
                saveRecord(filename_jsonRecord,path=workflow_folder_path)
            if not compile_success:compile_num += 1
        JsonRecord["Final"]=jsonContent
        saveRecord(filename_jsonRecord,path=workflow_folder_path)
        print("[+] Finished.")

    except Exception as e:
        print(f'{e}\n')
        print("---------------------------------------------------")
        print("| [x] Error exists, executable generation failed. |")
        print("---------------------------------------------------")
        return JsonRecord["Action list"],False,JsonRecord
    return
def workflow_sigmaRule(dict_input:dict={"higasa":"T1204	User Execution	Manual execution by user (opening LNK file)","id":str(uuid.uuid4())}):
    """
    這邊寫生成sigma rule的工作流程
    """
    #生成sigma rule
    sigmarule=sigmaruleGeneration(dict_input=dict_input)
    print(sigmarule)
    count=0
    #微調basic sigma rule
    sigmarule_refined=sigmaruleRefiner(dict_input={"unrefined_rule":sigmarule,"criteria":"detect by keywords but others"})
    print(sigmarule_refined)
    #整合basic sigma rule跟refined detecion rule
    result=sigmaCombination(dict_input={"basic sigma rule":sigmarule,"refined detection rule":sigmarule_refined})
    resultPattern=re.compile(r'<output>(.*?)</output>', re.DOTALL) 
    resultContent = resultPattern.findall(result)[0]
    filename=generate_secure_random_string(10)
    with open(os.path.join(os.getcwd(),"response","sigma",filename+"_sigmarule.yaml"),"w",encoding=settings.file_encoding)as f:
        f.write(resultContent)
    query=elasticSearchQueryDSLGeneration(resultContent)
    queryPattern=re.compile(r'<output>(.*?)</output>', re.DOTALL) 
    queryContent = queryPattern.findall(query)[0]
    print(queryContent)
    with open(os.path.join(os.getcwd(),"response",filename+"_query.yaml"),"w",encoding=settings.file_encoding)as f:
        f.write(queryContent)
    return queryContent
def workflow_RL(input:dict,max_step:int):
    """
    以input(可以是campaign,software,ctireport)
    """
    def initialize():
        return
    completion_task = False
    step = 0 
    plan ={}
    #
    while step < max_step or completion_task:
        12
        #把前面都丟給LLM回傳動作列表
        #識別動作並且執行
            ##動作列表
            
        #儲存記錄檔
        #更新agent獎勵
    return

def sigmaruleRefiner(dict_input:dict={},display:bool=False):
    print("[+]Start refining sigma rule.")
    """
    """
    SystemtPrompt=textLoader(txtName=f"SystemPrompt_sigmaruleRefiner")
    UserPrompt="<text>"+str(dict_input)+"</text>"
    messages = [
        {"role": "system", "content": SystemtPrompt},
        {"role": "user", "content": UserPrompt}
    ]
    if display:print(messages)
    sigmarule_refined=Llmrequest(messages)
    print("[-]Finish refining sigma rule.")
    return sigmarule_refined

def sigmaCombination(dict_input:dict={"basic sigma rule":"","refined detection rule":""},display:bool=False):
    print("[+]Start combining sigma rule.")
    """
    """
    SystemtPrompt=textLoader(txtName=f"SystemPrompt_sigmaCombination")
    UserPrompt="<text>"+str(dict_input)+"</text>"
    messages = [
        {"role": "system", "content": SystemtPrompt},
        {"role": "user", "content": UserPrompt}
    ]
    if display:print(messages)
    sigmarule_refined=Llmrequest(messages)
    print("[-]Finish combining sigma rule.")
    return sigmarule_refined

def elasticSearchQueryDSLGeneration(input:str="",display:bool=False):
    print("[+]Start generating query.")
    """
    """
    SystemtPrompt=textLoader(txtName=f"SystemPrompt_queryGeneration")
    UserPrompt="<text>"+input+"</text>"
    messages = [
        {"role": "system", "content": SystemtPrompt},
        {"role": "user", "content": UserPrompt}
    ]
    if display:print(messages)
    query=Llmrequest(messages)
    print("[-]Finish generating query.")
    return query

def elsticSearch_search(query,index:str="sagac1"):
    cmd = ["curl","-u", "elastic:1eqJXNpXocyu9EHg1*hO","-X", "GET",f"https://localhost:9200/{index}/_search?pretty","-H", "Content-Type: application/json","-d",json.dumps(query),"--insecure"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

if __name__ =='__main__':

    "	T1016	System Network Configuration Discovery	Uses IPCONFIG.EXE to discover IP address",
    "	T1053	Scheduled Task	Uses Task Scheduler to run other applications (Officeupdate.exe)"
    "	T1064	Scripting	Executes scripts (34fDFkfSD38.js)"
    "	T1106	Execution through API	Application (AcroRd32.exe) launched itself"
    "	T1059	Command-Line Interface	Starts CMD.EXE for commands (WinRAR.exe, wscript.exe) execution"
    "	T1016	System Network Configuration Discovery	Uses IPCONFIG.EXE to discover IP address"
    "	T1140	Deobfuscate/Decode Files or Information	certutil to decode Base64 binaries, expand.exe to decompress a CAB file"
    #label and description from saga c1
    #"detection condition":"keywords"
    dict_input={"higasa":"	T1016	System Network Configuration Discovery	Uses IPCONFIG.EXE to discover IP address"}
    #query=workflow_sigmaRule(dict_input=dict_input)
    #print(elsticSearch_search(query))
    #dict_input={"higasa":"T1204.002	User Execution	WINWORD.EXE triggered rFupMb75.exe (CreateFile)"}
    #query=workflow_sigmaRule(dict_input=dict_input)
    #print(elsticSearch_search(query))
    descriptionFromSaga=[
    "T1547.001	Boot or Logon Autostart Execution - Registry Run Keys/Startup Folder	Creates startup shortcut (sllauncherENU.dll (copy).lnk) via cscript.exe execution",
    "T1547.001	Boot or Logon Autostart Execution - Registry Run Keys/Startup Folder	Creates startup shortcut (sllauncherENU.dll (copy).lnk) via cscript.exe execution",
    "T1547.001	Boot or Logon Autostart Execution - Registry Run Keys/Startup Folder	Queries shortcut file information (sllauncherENU.dll (copy).lnk) using cscript.exe",
    "T1547.001	Boot or Logon Autostart Execution - Registry Run Keys/Startup Folder	Writes data to shortcut file (sllauncherENU.dll (copy).lnk) using cscript.exe",
    "T1547.001	Boot or Logon Autostart Execution - Registry Run Keys/Startup Folder	Closes shortcut file handle (sllauncherENU.dll (copy).lnk) using cscript.exe",#
    "T1082	System Information Discovery	Uses PowerShell.exe ($PSVersionTable) to gather system information (created by cscript.exe executing Retrive4075693065230196915.vbs)",#
    "T1016	System Network Configuration Discovery	Uses ipconfig.exe to discover IP address",
    "T1059	Scripting	Executes script using cscript.exe (Retrive4075693065230196915.vbs)",#
    "T1036.004	Masquerading: Masquerade Task or Service	Uses sc.exe to create a service pointing to 'sllauncherENU.dll (copy)'",#
    "T1053.005	Scheduled Task	Uses SCHTASKS.EXE to create a task that runs sllauncherENU.dll (copy)",
    "T1064	Scripting	Executes script using cscript.exe (Retrive4075693065230196915.vbs)",#
    "T1204.002	User Execution	cmd.exe created and executed Retrive4075693065230196915.vbs (CreateFile)",
    "T1204.002	User Execution	cmd.exe queried basic information of Retrive4075693065230196915.vbs (QueryBasicInformationFile)",
    "T1204.002	User Execution	cmd.exe wrote to Retrive4075693065230196915.vbs (WriteFile)",
    "T1204.002	User Execution	cmd.exe closed Retrive4075693065230196915.vbs (CloseFile)",
    "T1204.002	User Execution	cscript.exe executed Retrive4075693065230196915.vbs (Process Create)",
    "T1204.002	User Execution	WINWORD.EXE triggered rFupMb75.exe (CreateFile)",
    "T1204.002	User Execution	cmd.exe launched WINWORD.EXE via DDE (Process Create)"]
    #for i in descriptionFromSaga:
    #    print(i)
    #    dict_input={"higasa":i}
    #    query=workflow_sigmaRule(dict_input=dict_input)
    #    print(elsticSearch_search(query))
    query={
  "query": {
    "bool": {
      "must": [
        { "match": { "dstNode.Cmdline": "sc create win32times binPath= \"sllauncherENU.dll (copy)\"" }},
        { "match": { "dstNode.Image": "C:\\Windows\\system32\\sc.exe" }},
        { "match": { "dstNode.Name": "sc.exe" }},
        { "match": { "dstNode.Pid": 200 }},
        { "match": { "dstNode.Type": "Process" }},
        { "match": { "dstNode.UUID": "3a91904a-ab14-5b99-bb6e-87a13af812a9" }},
        { "match": { "label": "T1036.004_1f0614ea5c4af6faf1b44570f5f22f8a" }},
        { "match": { "relation": "Process Create" }},
        { "match": { "srcNode.Cmdline": "cscript //E:Jscript \"Retrive4075693065230196915.vbs\"" }},
        { "match": { "srcNode.Image": "C:\\Windows\\system32\\cscript.exe" }},
        { "match": { "srcNode.Name": "cscript.exe" }},
        { "match": { "srcNode.Pid": 5992 }},
        { "match": { "srcNode.Type": "Process" }},
        { "match": { "srcNode.UUID": "7a29affb-00d4-5a9a-89d2-3f3af08cf937" }},
        {
          "range": {
            "@timestamp": {
              "gte": "2022-06-14T04:20:05.000Z",
              "lte": "2022-06-14T04:20:05.000Z"
            }}}]}}}
    print(elsticSearch_search((query)))
    
