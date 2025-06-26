import subprocess

sigma_file = r"E:\Automatic-Malware-Generation-Using-LLMs\response\Wk7Cq6EDdt.yaml"

cmd = [
    "sigma", "convert",
    "-t", "esql", 
    "--without-pipeline",
    sigma_file
]

result = subprocess.run(cmd, capture_output=True, text=True)

# 輸出轉換結果
print(result.stdout)
