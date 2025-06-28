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
    with open(os.path.join(os.getcwd(),"response",filename+"_sigmarule.yaml"),"w",encoding=settings.file_encoding)as f:
        f.write(resultContent)
    query=elasticSearchQueryDSLGeneration(resultContent)
    queryPattern=re.compile(r'<output>(.*?)</output>', re.DOTALL) 
    queryContent = queryPattern.findall(query)[0]
    print(queryContent)
    with open(os.path.join(os.getcwd(),"response",filename+"_query.yaml"),"w",encoding=settings.file_encoding)as f:
        f.write(queryContent)
    return queryContent

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
    for i in descriptionFromSaga:
        print(i)
        dict_input={"higasa":i}
        query=workflow_sigmaRule(dict_input=dict_input)
        print(elsticSearch_search(query))

