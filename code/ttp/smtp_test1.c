#include <curl/curl.h>

int main() {
    CURL *curl;
    CURLcode res;
    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, "smtps://smtp.gmail.com:465");
        curl_easy_setopt(curl, CURLOPT_MAIL_FROM, "<nick5901879@gmail.com>");

        struct curl_slist *recipients = NULL;
        recipients = curl_slist_append(recipients, "<nick5901879@gmail.com>");
        curl_easy_setopt(curl, CURLOPT_MAIL_RCPT, recipients);

        curl_easy_setopt(curl, CURLOPT_USERNAME, "nick5901879@gmail.com");
        curl_easy_setopt(curl, CURLOPT_PASSWORD, "idrx tgeu qyix ozsr");

        const char *data = "To: target@example.com\r\n"
                           "From: your_email@gmail.com\r\n"
                           "Subject: 測試主旨\r\n"
                           "\r\n"
                           "這是一封來自 C++ 的 Gmail 郵件！\r\n";
        curl_easy_setopt(curl, CURLOPT_READFUNCTION, NULL);
        curl_easy_setopt(curl, CURLOPT_READDATA, data);
        curl_easy_setopt(curl, CURLOPT_UPLOAD, 1L);

        res = curl_easy_perform(curl);
        if(res != CURLE_OK)
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));

        curl_slist_free_all(recipients);
        curl_easy_cleanup(curl);
    }
    return 0;
}
