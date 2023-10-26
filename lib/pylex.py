
class Lexicon():
    def __init__(self, master):
        self.master = master
        self.create_path(self.master.project_dir)
        self.create_path(self.master.accounts_path)
        self.create_path(self.master.matches_path)

        self.master.ranks = self.read_json(path=self.master.ranks_path)
        self.master.agents = self.read_json(path=self.master.agents_path)
        self.master.reports_token = self.read_json(path=self.master.reports_token_path)

        self.master.config = self.read_json(path=self.master.config_path)
        if not self.master.config:
            self.master.config = {
                "region":"","client_version":"","season_id":None,
                "github_user":"","github_repo":"","github_token":"",
                "skip_download":False}
            print(self.master.config)
            self.save_file(self.master.json.dumps(self.master.config, indent=4), self.master.config_path)

        if not self.master.config.get("skip_download"):
            self.download_dependencies()

        self.master.lockfile_path = "".join([self.master.os.getenv("LOCALAPPDATA"), r"\Riot Games\Riot Client\Config\lockfile"])
        self.ansi_escape = self.master.re.compile(r'''
            \x1B  # ESC
            (?:   # 7-bit C1 Fe (except CSI)
                [@-Z\\-_]
            |     # or [ for CSI, followed by a control sequence
                \[
                [0-?]*  # Parameter bytes
                [ -/]*  # Intermediate bytes
                [@-~]   # Final byte
            )
        ''', self.master.re.VERBOSE)




    def save_file(self, content, path, attrib="w"):
        try:
            with open(path, attrib)as file:
                file.write(content)
        except Exception as e:
            print(" Error:",e)
    def read_file(self, path, attrib="r"):
        try:
            with open(path, attrib)as file:
                return file.read()
        except Exception as e:
            #print(" Error:",e)
            pass

    def read_json(self, content=None, path=None, attrib="r"):
        try:
            if not content == None:
                return self.master.json.loads(content)
            elif not path == None:
                return self.master.json.loads(self.read_file(path, attrib))
            else:
                print(" Error Json Load: No Content or Path.")
                return {}
        except Exception as e:
            return {}
    def create_path(self, path):
        if not self.master.os.path.exists(path):
            try:
                self.master.os.mkdir(path)
            except Exception as e:
                print(" Error:",e)

    def base64_encode(self, data):
        if isinstance(data, str): data = data.encode('ascii')
        return self.master.base64.b64encode(data).decode("ascii")

    def hex_to_RGB(self, hex):
        return [int(hex[i:i+2], 16) for i in range(1,6,2)]
    def RGB_to_hex(self, RGB):
        RGB = [int(x) for x in RGB]
        return "#"+"".join(["0{0:x}".format(v) if v < 16 else
                  "{0:x}".format(v) for v in RGB])
    def color_dict(self, gradient):
        return {"hex":[self.RGB_to_hex(RGB) for RGB in gradient],
            "r":[RGB[0] for RGB in gradient],
            "g":[RGB[1] for RGB in gradient],
            "b":[RGB[2] for RGB in gradient]}

    def linear_gradient(self, start_hex, finish_hex="#FFFFFF", n=10):
        s = self.hex_to_RGB(start_hex)
        f = self.hex_to_RGB(finish_hex)
        RGB_list = [s]
        for t in range(1, n):
          curr_vector = [
            int(s[j] + (float(t)/(n-1))*(f[j]-s[j]))
            for j in range(3)
          ]
          RGB_list.append(curr_vector)
        return self.color_dict(RGB_list)

    def polylinear_gradient(self, colors, n=1):
        n_out = int(float(n) / (len(colors) - 1))
        gradient_dict = self.linear_gradient(colors[0], colors[1], n_out)
        #print(gradient_dict)
        if len(colors) > 1:
          for col in range(1, len(colors) - 1):
            next = self.linear_gradient(colors[col], colors[col+1], n_out)
            for k in ("hex", "r", "g", "b"):
              gradient_dict[k] += next[k][1:]
        return gradient_dict['hex'][0]
    def download_dependencies(self):
        #self.master.refresh_change_state("PLEASE WAIT")
        url_list = [
            "https://valorant-api.com/v1/agents?isPlayableCharacter=true",
            "https://valorant-api.com/v1/competitivetiers",
            "https://valorant-api.com/v1/version"
            ]
        skins = {}
        #weapons = {}
        print(" Downloading Dependencies.")
        for url in url_list:
            print(" URL:",url)
            try:
                response = self.master.requests.get(url, timeout=10).json()['data']
            except Exception as e:
                response = None

            if response:
                with open("response.json","w")as file:
                    file.write(self.master.json.dumps(response))
                count = 0
                if url == "https://valorant-api.com/v1/agents?isPlayableCharacter=true":
                    #self.master.refresh_change_state("DOWNLOADING AGENTS [0:"+str(len(response))+"]")
                    for data in response:
                        colors_hold = []
                        for hex in data['backgroundGradientColors']:
                            colors_hold.append("#"+hex[:-2])
                        color_result = self.polylinear_gradient(colors_hold)
                        self.master.agents.update({data['uuid'].lower():{"name":data['displayName'],"color":color_result}})
                    self.save_file(self.master.json.dumps(self.master.agents, indent=4), self.master.agents_path)
                elif url == "https://valorant-api.com/v1/weapons/skins":
                    #self.master.refresh_change_state("DOWNLOADING SKINS")
                    for data in response:
                        if data['displayName']:
                            if not data['uuid'] in self.master.skins:
                                #is_found = False
                                for non in self.master.weapons:
                                    if not "-" in non:
                                        if non in data['displayName'].lower():
                                            #is_found = True
                                            skin_name = data['displayName'].lower()
                                            skin_name = skin_name.replace(" "+non, "")
                                            skin_name = skin_name.title()
                                            self.master.skins.update({data['uuid']:skin_name})
                    self.save_file(self.master.json.dumps(self.master.skins, indent=4), self.master.skins_path)

                elif url == "https://valorant-api.com/v1/weapons":
                    for data in response:
                        self.master.weapons.update({data['uuid']:data['displayName'],data['displayName'].lower():data['uuid']})
                    self.save_file(self.master.json.dumps(self.master.weapons, indent=4), self.master.weapons_path)
                elif url == "https://valorant-api.com/v1/competitivetiers":
                    response = response[-1]['tiers']
                    for data in response:
                        #print(rank)
                        tier_name = data['tierName'].title()
                        tier_color = "#"+data['color'][:-2]
                        if tier_name == "Unranked":
                            tier_color = (46, 46, 46)
                        #print(tier_color)
                        #if not str(data['tier']) in self.master.ranks:

                        self.master.ranks.update({data['tier']:{"name":tier_name,"color":tier_color}})
                    self.save_file(self.master.json.dumps(self.master.ranks, indent=4), self.master.ranks_path)
                    #self.master.time.sleep(.1)
                elif url == "https://valorant-api.com/v1/version":
                    self.master.config.update({"client_version":response['riotClientVersion']})
                    self.save_file(self.master.json.dumps(self.master.config, indent=4), self.master.config_path)
                elif url == "https://valorant-api.com/v1/maps":
                    for data in response:
                        map_url = data['mapUrl'].lower()
                        if not map_url in self.master.maps:
                            self.master.maps.update({map_url:data['displayName']})
                    self.save_file(self.master.json.dumps(self.master.maps, indent=4), self.master.maps_path)
                else:
                    print(" URL NOT FOUND:",url)
            self.master.time.sleep(1)





























#
