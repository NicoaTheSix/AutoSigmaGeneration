import re,os,time,json,random,subprocess,ollama,argparse,pandas as pd
from glob import glob
from tqdm import tqdm
from openai import OpenAI
import settings
import uuid
import argparse
import sys

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
    print("[+]Start generating KQL.")
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




def workflow1():
    print("Executing workflow 1")
    # TODO: Add your workflow1 logic here


def workflow2():
    print("Executing workflow 2")
    aaaa=["T1059	Command-Line Interface	Starts CMD.EXE for commands (WinRAR.exe, wscript.exe) execution","T1106	Execution through API	Application (AcroRd32.exe) launched itself","T1053	Scheduled Task	Loads the Task Scheduler DLL interface (Officeupdate.exe)","T1064	Scripting	Executes scripts (34fDFkfSD38.js)","T1204	User Execution	Manual execution by user (opening LNK file)","Persistence	T1060	Registry Run Keys / Startup Folder	Writes to a start menu file (Officeupdate.exe)","T1053	Scheduled Task	Uses Task Scheduler to run other applications (Officeupdate.exe)","Privilege Escalation	T1053	Scheduled Task	Uses Task Scheduler to run other applications (Officeupdate.exe)","Defense Evasion	T1064	Scripting	Executes scripts (34fDFkfSD38.js)","T1140	Deobfuscate/Decode Files or Information	certutil to decode Base64 binaries, expand.exe to decompress a CAB file","Discovery	T1012	Query Registry	Reads the machine GUID from the registry","T1082	System Information Discovery	Reads the machine GUID from the registry","T1016	System Network Configuration Discovery	Uses IPCONFIG.EXE to discover IP address"]
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
    for i in aaaa:
        print(i)
        dict_input={"higasa":i}
        query=workflow_sigmaRule(dict_input=dict_input)
        print(elsticSearch_search(query))

    # TODO: Add your workflow2 logic here


def workflow3():
    print("Executing workflow 3")
    # TODO: Add your workflow3 logic here
    with open(os.path.join(os.getcwd(),"response","VbGfW2bLcK_sigmarule.yml"),"r",encoding='utf-8')as f:
        resultContent=f .read()
    query=elasticSearchQueryDSLGeneration(resultContent)
    print(query)
    print(elsticSearch_search(query))
    return
def workflow4():
    print("Executing workflow 4")
    with open(os.path.join(os.getcwd(),"response","test.yml"),"r",encoding='utf-8')as f:
        Content=f .read()
    print(KQLGeneration(Content))
    # TODO: Add your workflow4 logic here


def workflow5():
    print("Executing workflow 5")
    # TODO: Add your workflow5 logic here

    for i in os.listdir(os.path.join(os.getcwd(),"C1_rule")):
        print(i)
        with open(os.path.join(os.getcwd(),"C1_rule",i),"r",encoding='utf-8')as f:
            Content=f.read()
        query_KQL=KQLGeneration(Content)
        print(query_KQL)
        with open(os.path.join(os.getcwd(),"response",i.split(".")[0]+"_KQLquery.txt"),"w",encoding='utf-8')as f:
            f.write(query_KQL)
        #print(KQLGeneration(Content))
    

def workflow6():
    print("Executing workflow 6")
    # TODO: Add your workflow6 logic here


def workflow7():
    print("Executing workflow 7")
    # TODO: Add your workflow7 logic here


def workflow8():
    print("Executing workflow 8")
    # TODO: Add your workflow8 logic here


def workflow9():
    print("Executing workflow 9")
    # TODO: Add your workflow9 logic here


def workflow10():
    print("Executing workflow 10")
    # TODO: Add your workflow10 logic here


# Mapping of input choices to workflow functions
WORKFLOWS = {
    '1': workflow1,
    '2': workflow2,
    '3': workflow3,
    '4': workflow4,
    '5': workflow5,
    '6': workflow6,
    '7': workflow7,
    '8': workflow8,
    '9': workflow9,
    '10': workflow10,
}

def main():
    parser = argparse.ArgumentParser(
        description='CLI to execute predefined workflows (1-10).'
    )
    parser.add_argument(
        'workflow',
        choices=WORKFLOWS.keys(),
        help='Workflow number to execute (1-10)'
    )
    args = parser.parse_args()

    # Execute the selected workflow
    func = WORKFLOWS[args.workflow]
    func()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # No arguments provided, show help
        print("Please specify a workflow number (1-10).\n")
        parser = argparse.ArgumentParser(
            description='CLI to execute predefined workflows (1-10).'
        )
        parser.print_help()
        sys.exit(1)

    main()


