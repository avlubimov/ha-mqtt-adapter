import sys


class Logger:
    """
    Простой логгер, выводит в stderr или stdout

    """
    def __init__(self, verbose, output=sys.stderr):
        """

        :param verbose: число от 1 и до 3 где 1 минимум, а 3 debug
        :param output: sys.stderr или sys.stdout
        """
        self.verbose = verbose
        self.output = output

    def msg(self, msg):
        print(msg, file=self.output)

    def msg_info(self, msg):
        if self.verbose > 0:
            self.msg(f"Info: {msg}")

    def msg_debug(self, msg):
        if self.verbose > 1:
            self.msg(f"Debug: {msg}")

    def msg_error(self, msg):
        self.msg(f"Error: {msg}")
