from optparse import OptionParser


class Parser(OptionParser):
    def __init__(self):
        super().__init__()
        self.add_option("-v", action="count", dest="verbose", help="verbose")
        self.add_option("-c", action="store", dest="config_file", help="", default="cfg.ini")
        self.options, self.args = self.parse_args()
