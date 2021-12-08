from rotating_proxies.policy import BanDetectionPolicy

class AmazonPolicy(BanDetectionPolicy):
    def response_is_ban(self, request, response):
        # use default rules, but also consider HTTP 200 responses
        ban = super(AmazonPolicy, self).response_is_ban(request, response)
        ban = ban or ('captcha' in response.url) or ('captcha' in str(response.body))
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)

        # print("{}\n{}".format(response.url, response.text))

        # return True
        # if response.status == 200:
        #     return True
        return ban

    def exception_is_ban(self, request, exception):
        # override method completely: don't take exceptions in account
        return None