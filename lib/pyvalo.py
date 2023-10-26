is_log = True
def log(*argv):
    if is_log:
        text = ""
        for arg in argv:
            text += str(arg)
        print(text)
chrome_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
class LocalClient:
    def __init__(self, master):
        self.master = master
        self.session = self.master.requests.Session()
        if self.master.config.get('log') == False: global is_log; is_log=False
        self.lockfile = self.get_lockfile()
        if not self.master.config.get('region'): self.get_region()
        self.region = self.master.config['region']
        self.token = None
        self.entitlement = None
        self.client_version = self.master.config.get("client_version")
        self.season_id = self.get_season_id()

    def local(self, path, headers={}, payload={}, method='get'):
        url = "{}://127.0.0.1:{}{}".format(self.lockfile[4],self.lockfile[2],path)
        if method.lower() == 'post':
            try:
                response = self.session.post(url, headers=headers, json=payload, auth=('riot', self.lockfile[3]), verify=self.master.ssl.CERT_NONE, timeout=10)
            except Exception as e:
                log(" Error:",e)
                return {}
        else:
            try:
                response = self.session.get(url, headers=headers, json=payload, auth=('riot', self.lockfile[3]), verify=self.master.ssl.CERT_NONE, timeout=10)
            except Exception as e:
                log(" Error:",e)
                return {}
        data = self.master.lex.read_json(content=response.content)
        if response.ok:
            if data:
                return data
            else:
                return True
        print(' error status:',data)
        return {}


    def remote(self, url, headers=None, data={}, method='get', retry=False):
        if not self.token or not self.entitlement: self.get_entitlements()
        if headers == None:
            headers = self.get_headers()
        if method.lower() == 'post':
            pass
        else:
            try:
                response = self.session.get(url, headers=headers, data={}, timeout=5)
            except Exception as e:
                print(" Error:",e); return {}
        data = self.master.lex.read_json(content=response.content)

        if response.ok:
            return data
        else:
            error_message = data.get("message")
            if error_message:
                log(' error message:',data.get('message'))
                if "Failure validating/decoding RSO Access Token" in error_message or "Invalid RSO token" in error_message:
                    if retry == False:
                        self.get_entitlements()
                        return self.remote(url, headers, data, method, True)
            return {}
        print(' error status:',data.get('message'))
        return {}

    def get_session(self):
        return self.local("/chat/v1/session")
    def get_presences(self):
        return self.local("/chat/v4/presences")
    def get_entitlements(self) -> dict:
        response = self.local("/entitlements/v2/token")
        if response: self.token = response['authorization']['accessToken']['token']; self.entitlement = response['token']
    def get_help(self):
        return self.local("/help")
    def get_local_swagger(self):
        return self.local("/swagger/v3/openapi.json")

    def get_region(self):
        log(' getting region')
        if self.check_lockfile():
            response = self.local("/product-session/v1/external-sessions")
            for id in response:
                if not id == "host_app":
                    for arg in response[id]['launchConfiguration']['arguments']:
                        if "-ares-deployment=" in arg:
                            self.master.config.update({"region":arg.replace("-ares-deployment=","")})
                            self.master.lex.save_file(self.master.json.dumps(self.master.config, indent=4), self.master.config_path)
                            return
        exit(' Please open Valorant to get region, or set in config file.')

    def get_lockfile(self):
        lockfile_path = "".join([self.master.os.getenv("LOCALAPPDATA"), r"\Riot Games\Riot Client\Config\lockfile"])
        data = self.master.lex.read_file(lockfile_path)
        if data: return data.split(":")
        return
        self.base_url = f"{data[4]}://127.0.0.1:{data[2]}"
        self.session.auth = ("riot", data[3])
        return data
    def check_lockfile(self):
        if not self.lockfile: self.lockfile = self.get_lockfile()
        if self.lockfile: return True

    def get_match_id(self, puuid, state):
        log(" Getting Match ID")
        if state == "INGAME":
            state_hold = 'INGAME'
            response = self.remote("https://glz-ap-1.ap.a.pvp.net/core-game/v1/players/"+puuid)
        elif state == "PREGAME":
            state_hold = 'PREGAME'
            response = self.remote("https://glz-ap-1.ap.a.pvp.net/pregame/v1/players/"+puuid)
        else:
            state_hold = 'PREGAME'
            response = self.remote("https://glz-ap-1.ap.a.pvp.net/pregame/v1/players/"+puuid)
            if not response: response = self.remote("https://glz-ap-1.ap.a.pvp.net/core-game/v1/players/"+puuid); state_hold = 'INGAME'
        if response.get('MatchID'): return (response['MatchID'], state_hold)
        return (None, state)

    def get_match_info(self, game_id, state):
        log(" Getting Match Info")
        if state == "INGAME":
            return self.remote("https://glz-ap-1.ap.a.pvp.net/core-game/v1/matches/"+game_id)
        elif state == "PREGAME":
            return self.remote("https://glz-ap-1.ap.a.pvp.net/pregame/v1/matches/"+game_id)
        print(" Error: match info session state.")
        return {}


    def get_match_history(self, puuid):
        #puuid = "bfb6ad7e-40a0-5855-85be-f13d18572e68"
        log(" Getting Match History")
        start_index = 0
        end_index = 25
        response = self.remote("https://pd.{}.a.pvp.net/match-history/v1/history/{}?startIndex={}&endIndex={}".format(self.region,puuid,start_index,end_index))
        return response['History'] if response.get("History") else []

    def get_match_details(self, match_id):
        #log(" Getting Match Details: ",match_id)
        return self.remote("https://pd.{}.a.pvp.net/match-details/v1/matches/{}".format(self.region,match_id))

    def get_report_token(self, match_id, puuid):
        return self.remote("https://pd.ap.a.pvp.net/restrictions/v1/playerReportToken/{}/{}".format(match_id,puuid))

    def report_player(self, puuid, token):
        report_categories = ["COMMS ABUSE - TEXT","COMMS ABUSE - VOICE","CHEATING","LEAVING THE GAME / AFK","OFFENSIVE OR INAPPROPRIATE NAME","SABOTAGING THE TEAM","DISRESPECTFUL BEHAVIOR","THREATS"]
        data = {
            "categories":["COMMS ABUSE - TEXT","COMMS ABUSE - VOICE","LEAVING THE GAME / AFK","SABOTAGING THE TEAM","DISRESPECTFUL BEHAVIOR","THREATS"],
            "location":"in-game",
            "offenderId":puuid,
            "token":token,
            "tokenType":"MATCH_TOKEN"
        }
        return self.local("/player-reporting/v2/report", payload=data, method='post')

    def get_season_id(self):
        log(" Getting Season ID")
        content_response = self.remote("https://shared.ap.a.pvp.net/content-service/v3/content")
        if content_response.get('Seasons'):
            for season in content_response['Seasons']:
                if season['IsActive'] and season['Type'] == "act":
                    self.master.config.update({"season_id":season['ID']})
                    self.master.lex.save_file(self.master.json.dumps(self.master.config, indent=4), self.master.config_path)
                    return season['ID']
        else:
            return self.master.config.get("season_id")

    def get_headers(self):
        headers = {
            "X-Riot-ClientPlatform":"ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9",
            "X-Riot-ClientVersion":self.client_version,
            "X-Riot-Entitlements-JWT":self.entitlement,
            "Authorization": "Bearer "+self.token
            }
        return headers

    def get_name_tag(self, puuid) -> dict:
        response = self.remote("https://api.henrikdev.xyz/valorant/v1/by-puuid/account/{}".format(puuid), headers={})
        if response: return (response['data'].get('name'),response['data'].get('tag'))
    def get_mmr(self, puuid):
        response = self.remote("https://pd.ap.a.pvp.net/mmr/v1/players/{}".format(puuid))
        if response:
            try:
                tier = response['QueueSkills']['competitive']['SeasonalInfoBySeasonID'][self.season_id]['CompetitiveTier']
                rating = response['QueueSkills']['competitive']['SeasonalInfoBySeasonID'][self.season_id]['RankedRating']
                return (tier,rating)
            except Exception as e:
                #log(" Error Data:",e)
                return (0,0)


    def get_lifetime_matches(self, puuid) -> dict:
        matches = {}
        if self.master.config.get('season_id'):
            response = self.remote("https://api.henrikdev.xyz/valorant/v1/by-puuid/lifetime/matches/ap/"+puuid, headers={})
            if response:
                format_string = "%Y-%m-%dT%H:%M:%S.%fZ"
                for data in response['data']:
                    if data['meta']['season']['id'] == self.master.config['season_id']:
                        _ts = self.master.datetime.datetime.strptime(data['meta']['started_at'], format_string).timestamp()
                        matches.update({data['meta']['id']:{'start_time':int(_ts),'queue_id':data['meta']['mode']}})
        return matches
































#
