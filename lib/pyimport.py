import urllib3
urllib3.disable_warnings()
#from colr import color
class Import():
    def __init__(self, master):
        self.master = master

        self.master.ranks_image_path = "ranks\\"
        self.master.skins_image_path = "skins\\"
        self.master.agents_image_path = "agents\\"
        self.master.config_path = "config.json"
        self.master.weapons_path = "weapons.json"

        self.master.re = __import__("re")
        self.master.os = __import__("os")
        self.master.os.system('cls'),print("")
        self.master.ssl = __import__("ssl")
        self.master.json = __import__("json")
        self.master.time = __import__("time")
        #self.master.numpy = __import__("numpy")
        self.master.base64 = __import__("base64")
        self.master.hashlib = __import__("hashlib")
        #self.master.urllib3 = __import__("urllib3")
        self.master.requests = __import__("requests")
        self.master.session = self.master.requests.Session()
        self.master.datetime = __import__("datetime")
        self.master.threading = __import__("threading")
        #self.master.Image = getattr(__import__("PIL", fromlist=["Image"]),"Image")
        self.master.color = getattr(__import__("colr", fromlist=["color"]),"color")

        home_dir = self.master.os.path.expanduser('~')+"\\"
        self.master.project_dir = home_dir+"valocli\\"
        self.master.accounts_path = self.master.project_dir+"accounts\\"
        self.master.matches_path = self.master.project_dir+"matches\\"
        self.master.maps_path = self.master.project_dir+"maps.json"
        self.master.ranks_path = self.master.project_dir+"ranks.json"
        self.master.skins_path = self.master.project_dir+"skins.json"
        self.master.notes_path = self.master.project_dir+"notes.json"
        self.master.agents_path = self.master.project_dir+"agents.json"
        self.master.weapons_path = self.master.project_dir+"weapons.json"
        self.master.reports_token_path = self.master.project_dir+"reports_token.json"


























#
