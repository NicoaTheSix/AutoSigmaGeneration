import subprocess
import json
def queryTranslator():
    sigma_file = r"E:\Automatic-Malware-Generation-Using-LLMs\response\IdaVw3lbvf.yaml"
    cmd = ["sigma", "convert","-t", "esql","--without-pipeline",sigma_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    query=result.stdout
    return query

index = "sagac1"
queryTranslator_result = queryTranslator().strip()  # 要把末尾的換行符去掉

payload = {
    "query": queryTranslator_result
}

cmd = [
    "curl",
    "-u", "elastic:1eqJXNpXocyu9EHg1*hO",
    "-X", "POST",
    f"https://localhost:9200/{index}/_query?pretty",
    "-H", "Content-Type: application/json",
    "-d", json.dumps(payload),
    "--insecure"
]

result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)