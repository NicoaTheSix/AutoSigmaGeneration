import os
import time
import json
import secrets
import string

# Encoding
file_encoding = "utf-8"
# Paths
"""
when using Github Desktop to open the source directory
home path should be \'...\\Malicious_Code_Generation \'
home_path is the main directory of the project

The name of responce_title is based on the time.
""" 
source                  ="openai"#"ollama"
llm                     ="gpt-4o-mini"#"llama3.2"
home_path               = os.getcwd()
response_title          = time.strftime("%Y%m%d%H%M",time.localtime())
response_folder_path    = os.path.join(home_path,"response")
targetOS               ="Windows 11"
##the folders below should be created during the process of the program

#Dataset for action list
dir_ttp                 = os.path.join(home_path,"ttp_with_procedure")
dict_ttp                = os.path.join(home_path,"dict_technique.json") 
csv_ttp                 = os.path.join(home_path,"techniques.csv")        
csv_ttp_noPr            = os.path.join(home_path,"techniques_noPr.csv")        
with open(dict_ttp, 'r', encoding = file_encoding) as Json:
    dictionary_technique=json.load(Json)
##the unique directory the user has to set on their own is the directory of cti report
dir_cti                 = os.path.join("D:\\","all_CTI_report")

# Directory Structure
dir_struct = {
    'response': {
        'tasks': {},
    }
}
# 紀錄格式

global JsonRecord
JsonRecord={"Error":[],
            "Settings":{
                "source":source,
                "llm":llm,
                "title of the Response":response_title},
            "Input":{},
            "Code review":{},
            "Debug":{},
            "Main code review":{},
            "Responce":{}
            }
class ProjectEnvironmentSettingError(Exception):
    def __init__(self, message):
        self.message=message
        super().__init__(self.message)
    def __init__(self):
        self.message="There's something wrong in setting.\nPlease check setting.py once more."
        super().__init__(self.message)
def UI_initiate():
    title_=f"""
=======================================
Automatic-Malware-Generation-Using-LLMs
--from AntLab in NTUST-----------------
=======================================
"""
    print(title_)
    return
def generate_secure_random_string(length):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))
def create_dir(homePath: str, dirStruct: dict):
    for directory, subStructure in dirStruct.items():
        path = os.path.join(homePath, directory)
        #print(path)
        os.makedirs(path, exist_ok=True)                # Create the directory if it doesn't exist
        create_dir(path, subStructure)                  # Recursively create subdirectories
#display the origin name of variable
def namestr(obj):
    try:
        namespace=globals()
        return [name for name in namespace if namespace[name] is obj]
    except:
        namespace=locals()
        return [name for name in namespace if namespace[name] is obj]
def split_line(bool_display:bool=False):
    split_line="================================="
    if bool_display:print("{:>38} {:<30}".format(split_line,""))   
    return
#test
def saveRecord(filename_jsonRecord:str,path:str=""):
    """
    將過程記錄在Json中，方便實驗過程檢驗或是查看各項細節
    由於workflow啟動同時會自動以當下時間以及其他參數作為json檔案名稱且儲存位置固定所以只傳入檔案名稱即可
    """
    if path == "":
        with open(os.path.join(response_folder_path,filename_jsonRecord), mode = 'w', encoding=file_encoding) as LogFile:
            json.dump(JsonRecord,LogFile,indent=4)
        return
    else: 
        with open(os.path.join(path,filename_jsonRecord), mode = 'w', encoding=file_encoding) as LogFile:
            json.dump(JsonRecord,LogFile,indent=4)
        return
def loadSettings(bool_display:bool=False):
    """
    以下這些檔案都是檢查是否存在
    """
    def display_and_exist(path:str):
        formatted_key = namestr(path)[0]
        space=" "
        if bool_display:print("{:>5}-{:<30}:   {:<60}".format(space,formatted_key,path))
        os.makedirs(path,exist_ok=True)
        return    
    def display_and_exist_create_Json(path:str):
        formatted_key = namestr(path)[0]
        space=" "
        if bool_display:print("{:>5}-{:<30}:   {:<60}".format(space,formatted_key,path))
        with open(path, 'w', encoding = file_encoding) as responseJson:
            json.dump({}, responseJson, indent = 4)
        return    
    def display_and_exist_load_Json(path:str):
        formatted_key = namestr(path)[0]
        space=" "
        if bool_display:print("{:>5}-{:<30}:   {:<60}".format(space,formatted_key,path))
        with open(path, 'r', encoding = file_encoding) as Json:
            json.load(Json)
        return
    def display_and_exist_addition(path:str):
        formatted_key = namestr(path)[0]
        space=" "
        if bool_display:print("{:>5}-{:<30}:   {:<60}".format(space,formatted_key,path))
        #print(f"   {os.path.exists(path)}")
        #print(f"    {os.listdir(path)}")
        return
    try:
        UI_initiate()
        create_dir(homePath=home_path,dirStruct=dir_struct)   
        print("[+] Creating directory structure")
        split_line()     
        if bool_display:print("     Directory Status")
        split_line()
        if bool_display:print(f"     Check the automatic setting in the repository.")
        split_line()     
        display_and_exist(home_path)
        display_and_exist(response_folder_path)
        #display_and_exist_create_Json(code_json_file_path)
        #display_and_exist(code_output_path)
        #display_and_exist(code_review_output_path)
        #display_and_exist(code_debug_output_path)
        split_line()
        display_and_exist(dir_ttp)
        display_and_exist_addition(csv_ttp)
        display_and_exist_addition(csv_ttp_noPr)
        display_and_exist_load_Json(dict_ttp)
        split_line()     
        if bool_display:print("     Check User setting")
        split_line()     
        display_and_exist_addition(dir_cti)
        split_line()     
        if bool_display:print(f"     API-key:{os.getenv('OPENAI_API_KEY') != None}")
        split_line()     
    
        print("[-] Directory checking Finish")
    except:
        raise ProjectEnvironmentSettingError()
    return
def settingPath(filename:str):
    global workflow_folder_path
    global code_output_path
    global code_review_output_path
    global code_debug_output_path
    global code_json_file_path
    return
#for testing
if __name__ == "__main__":
    
    loadSettings()
"""
try:
    raise ProjectEnvironmentSettingError()
except ProjectEnvironmentSettingError as e:
    print(f"ww{e}")"""