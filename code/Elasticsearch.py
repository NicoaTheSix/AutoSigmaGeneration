import subprocess
import json
def queryTranslator():
    sigma_file = r"E:\Automatic-Malware-Generation-Using-LLMs\response\IdaVw3lbvf.yaml"
    cmd = ["sigma", "convert","-t", "esql","--without-pipeline",sigma_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    query=result.stdout
    return query
def elsticSearch_search(query):
    cmd = ["curl","-u", "elastic:1eqJXNpXocyu9EHg1*hO","-X", "GET",f"https://localhost:9200/{index}/_search?pretty","-H", "Content-Type: application/json","-d",query,"--insecure"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout
query = {
    "query": {
        "match": {
            "user.name": "root"
        }
    }
}
#print()
index = "sagac1"  # 你的 index 名稱

query=json.dumps(query)#
#query=f"""{json.dumps({"query":queryTranslator()})}"""
print(query)
print(elsticSearch_search(query))