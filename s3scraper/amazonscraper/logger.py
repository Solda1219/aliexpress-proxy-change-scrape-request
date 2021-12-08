class AmazonLogPrinter:
    instance = None
    logs = None

    def __init__(self, text: str):
        if text is not None:
            if not AmazonLogPrinter.instance:
                AmazonLogPrinter.instance = AmazonLogPrinter(None)
                AmazonLogPrinter.instance.logs = []
            print(text)
            AmazonLogPrinter.instance.logs.append(text + "\n")

    @staticmethod
    def export(filename):
        with open(filename, 'w+') as logfile:
            logfile.writelines(AmazonLogPrinter.instance.logs)
