from rotating_proxies.policy import BanDetectionPolicy


class TPPolicy(BanDetectionPolicy):
    def response_is_ban(self, request, response):
        # use default rules, but also consider HTTP 200 responses
        ban = super(TPPolicy, self).response_is_ban(request, response)
        ban = ban or ('captcha' in response.url) or ('captcha' in str(response.body))
        return ban

    def exception_is_ban(self, request, exception):
        # override method completely: don't take exceptions in account
        return None
