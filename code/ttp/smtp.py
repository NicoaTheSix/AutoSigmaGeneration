import smtplib
smtp=smtplib.SMTP('smtp.gmail.com', 587)
smtp.ehlo()
smtp.starttls()
smtp.login('nick5901879@gmail.com','idrx tgeu qyix ozsr')
from_addr='gaojiheng142@gmail.com'
to_addr="nick5901879@gmail.com"
msg="Subject:Gmail sent by Python scripts\nHello World!"
status=smtp.sendmail(from_addr, to_addr, msg)#加密文件，避免私密信息被截取
if status=={}:
    print("郵件傳送成功!")
else:
    print("郵件傳送失敗!")
smtp.quit()