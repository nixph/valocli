class Main:
    def __init__(self, master):
        self.master = master

    def session(self):
        response = self.master.valo.get_session()
        if response.get('state') == 'connected':
            self.master.connected = True
            self.match_history(response['puuid'], True)
            #self.get_match_history(response['puuid'], True)
            print(" Connected:",response['puuid'])
            return {'puuid':response['puuid'],'name':response['game_name'],'tag':response['game_tag']}
        else:
            self.master.connected = False
            self.master.time.sleep(10)

    def presences(self):
        response = self.master.valo.get_presences()
        #print(response)
        #exit()
        presences = {}
        if response.get('presences'):
            response = sorted(response['presences'], key=lambda d: (d['game_name']+"#"+d['game_tag']).lower())
            for data in response:
                try:
                    convertbytes = data['private'].encode("ascii")
                    convertedbytes = self.master.base64.b64decode(convertbytes)
                    private = self.master.json.loads(convertedbytes.decode("ascii"))
                except Exception as e:
                    private = None
                if private:
                    presences.update({
                        data['puuid']:{
                            "name":data.get("game_name"),
                            "tag":data.get("game_tag"),
                            "map":private.get("matchMap"),
                            "rank":private.get("competitiveTier"),
                            "queue_id":private.get("queueId"),
                            "party":private['partyId'],
                            "party_size":private.get("partySize"),
                            "party_state":private.get("partyState"),
                            "session_state":private.get("sessionLoopState"),
                            "party_session_state":private.get("partyOwnerSessionLoopState"),
                            "level":private['accountLevel'],
                            "ally_score":private.get("partyOwnerMatchScoreAllyTeam"),
                            "enemy_score":private.get("partyOwnerMatchScoreEnemyTeam")
                        }})
        return presences

    def get_backup_data(self, puuid):
        data = self.master.lex.read_json(path=self.master.accounts_path+puuid)
        if not data:
            #print(" backup data not found:",puuid)
            response = self.master.github.get_content('accounts/'+puuid)
            #response = {}
            if response.get('content'):
                data = self.master.lex.read_json(content=self.master.base64.b64decode(response['content']))
            else:
                #print(" github account not found:",puuid)
                data = {'name':'','tag':'','note':'','matches':[],'reports':[]}
        if not 'matches' in data: data.update({'matches':[]})
        if not 'reports' in data: data.update({'reports':[]})
        return data

    def upload_backup_data(self, puuid, data):
        upload_response = {}
        if not self.master.github.accounts_sha == None:
            if self.master.github.accounts_sha.get(puuid):
                if not self.master.github.hash(data) == self.master.github.accounts_sha.get(puuid):
                    #print(" updating github account:",puuid)
                    upload_response = self.master.github.upload_content('accounts/'+puuid, self.master.lex.base64_encode(data), self.master.github.accounts_sha[puuid])
            else:
                #print(" uploading github account:",puuid)
                upload_response = self.master.github.upload_content('accounts/'+puuid, self.master.lex.base64_encode(data))
        if upload_response.get('content'): self.master.github.accounts_sha.update({puuid:upload_response['content']['sha']})

    def upload_match_data(self, _match_id, data):
        upload_response = {}
        if not self.master.github.matches_sha == None:
            if self.master.github.matches_sha.get(_match_id):
                if not self.master.github.hash(data) == self.master.github.matches_sha[_match_id]:
                    upload_response = self.master.github.upload_content('matches/'+_match_id, self.master.lex.base64_encode(data), self.master.github.matches_sha[_match_id])
            else:
                upload_response = self.master.github.upload_content('matches/'+_match_id, self.master.lex.base64_encode(data))
        if upload_response.get('content'): self.master.github.matches_sha.update({_match_id:upload_response['content']['sha']})

    def matches_fix(self, match_list):
        new_matches = {}
        for m_id in match_list:
            if not self.is_match_exists(m_id):
                for i in range(0,3):
                    m_details = self.master.valo.get_match_details(m_id)
                    if m_details:
                        m_processed = self.match_info(m_details)
                        self.master.lex.save_file(self.master.json.dumps(m_processed, indent=4), self.master.matches_path+m_id)
                        break
                    self.master.time.sleep(1)
            if self.is_match_exists(m_id):
                m_processed = self.master.lex.read_json(path=self.master.matches_path+m_id)
                new_matches.update({m_id:m_processed.get('season_id')})
            else:
                new_matches.update({m_id:None})
        return new_matches

    def clean_old_matches(self, matches_dict):
        if self.master.config.get('season_id'):
            remove_list = []
            for m_id in matches_dict:
                if matches_dict[m_id]:
                    if not matches_dict[m_id] == self.master.config['season_id']:
                        remove_list.append(m_id)
            for m_id in remove_list:
                matches_dict.pop(m_id)
        return matches_dict
    def check_unknown_matches(self):
        dir_list = self.master.os.listdir(self.master.accounts_path)
        for puuid in dir_list:
            backup_data = self.get_backup_data(puuid)
            for m_id in backup_data['matches']:
                if not backup_data['matches'][m_id]:
                    print(puuid)
                    m_details = self.master.valo.get_match_details(m_id)
                    if m_details:
                        m_processed = self.match_info(m_details)
                        backup_data['matches'][m_id] = m_processed.get('season_id')
                        self.master.lex.save_file(self.master.json.dumps(m_processed, indent=4), self.master.matches_path+m_id)
            self.master.lex.save_file(self.master.json.dumps(backup_data, indent=4), self.master.accounts_path+puuid)

    def clean_old_reports(self, matches_dict, reports_dict):
        remove_list = []
        for m_id in reports_dict:
            if not m_id in matches_dict:
                remove_list.append(m_id)
        for m_id in remove_list:
            try:
                reports_dict.remove(m_id)
            except Exception as e:
                print(" Error:",e)
        return reports_dict
    def is_match_exists(self, mid):
        if self.master.os.path.exists(self.master.matches_path+mid): return True
    def match_history(self, puuid, is_init=False):
        self.check_unknown_matches()
        if is_init:
            backup_data = self.get_backup_data(puuid)
            if isinstance(backup_data.get('matches'), list): backup_data['matches'] = self.matches_fix(backup_data['matches'])

            backup_data['matches'] = self.clean_old_matches(backup_data['matches'])
            backup_data['reports'] = self.clean_old_reports(backup_data['matches'], backup_data['reports'])
            self.master.lex.save_file(self.master.json.dumps(backup_data, indent=4), self.master.accounts_path+puuid)

        response = self.master.valo.get_match_history(puuid)
        match_list = [x['MatchID'] for x in response if x['QueueID']]
        text = " Downloading Match [{}:{}]".format(0,len(match_list))
        print(text, end="\r")
        count = 0
        for match_id in match_list:
            if not self.is_match_exists(match_id):
                match_details = self.master.valo.get_match_details(match_id)
                if match_details:
                    match_processed = self.match_info(match_details)
                    self.master.lex.save_file(self.master.json.dumps(match_processed, indent=4), self.master.matches_path+match_id)
            count += 1
            print(" "*len(text), end="\r")
            text = " Downloading Match [{}:{}]".format(count,len(match_list))
            print(text, end="\r")
        print("")
        match_found = []
        match_count = 0
        text = " Uploading Match to Github [{}:{}]".format(0,len(match_list))
        print(text, end="\r")
        for match_id in match_list:
            match_count += 1
            if self.is_match_exists(match_id):
                match_found.append(match_id)
                self.upload_match_data(match_id, self.master.lex.read_file(self.master.matches_path+match_id))
                match_details = self.master.lex.read_json(path=self.master.matches_path+match_id)
                player_count = 0
                for puuid in match_details['players']:
                    upload_response = {}
                    player_count += 1
                    backup_data = self.get_backup_data(puuid)
                    if isinstance(backup_data.get('matches'), list): backup_data['matches'] = self.matches_fix(backup_data['matches'])
                    if not 'matches' in backup_data: backup_data.update({"matches":{}})
                    if not 'reports' in backup_data: backup_data.update({"reports":[]})
                    if not match_id in backup_data['matches'] and match_details.get('season_id'):
                        backup_data['matches'].update({match_id:match_details['season_id']})

                    self.master.lex.save_file(self.master.json.dumps(backup_data, indent=4), self.master.accounts_path+puuid)
                    self.upload_backup_data(puuid, self.master.json.dumps(backup_data, indent=4))

                    print(" "*len(text), end="\r")
                    text = " Uploading Match to Github [{}:{}][{}:{}]".format(match_count,len(match_list),player_count,len(match_details['players']))
                    print(text, end="\r")
        print("")
        match_found = match_found[0:10]
        match_found.reverse()
        if match_found: self.master.match_history = match_found
        #exit()


    def get_match_history(self, puuid, is_init=False):

        #report_token_response = self.master.valo.get_report_token('a59323d4-b57d-4c4c-9646-be90b0c34646', '0d788cd4-210f-5b8d-a67a-43231ba8ddfd')
        #print(report_token_response)



        #return
        print(" Downloading Match History.")
        match_history = {}
        if is_init:
            pass
            match_history = self.master.valo.get_lifetime_matches(puuid)
            for match_id in match_history:
                match_details = self.master.valo.get_match_details(match_id)
                self.master.lex.save_file(self.master.json.dumps(match_details, indent=4), 'match.json')
                #print(match_details)
                break
            #print(match_history)
            #print(len(match_history))
        exit()
        if not match_history:
            match_history_response = self.master.valo.get_match_history(puuid)
            for data in match_history_response:
                match_history.update({data['MatchID']:{'start_time':data['GameStartTime'],'queue_id':data['QueueID']}})
        print(match_history)
        print(len(match_history))
        exit()
        print("")
        text = " Downloading Match [{}:{}]".format(0,len(match_history))
        print(text, end="\r")
        count = 0
        for match_id in match_history:
            if not self.master.os.path.exists(self.master.matches_path+match_id) and match_history[match_id]['queue_id']:
                match_details = self.master.valo.get_match_details(match_id)
                if match_details:
                    match_processed = self.match_info(match_details)
                    self.master.lex.save_file(self.master.json.dumps(match_processed, indent=4), self.master.matches_path+match_id)
                else:

                    print("error id:",match_id)
                    exit()
            count += 1
            print(" "*len(text), end="\r")
            text = " Downloading Match [{}:{}]".format(count,len(match_history))
            print(text, end="\r")
        print("")
        match_found = []
        match_count = 0

        text = " Uploading Match Data to Github [{}:{}]".format(0,len(match_history))
        print(text, end="\r")
        for match_id in match_history:
            match_count += 1
            if self.master.os.path.exists(self.master.matches_path+match_id):
                match_found.append(match_id)
                if not self.master.github.matches == None:
                    if not match_id in self.master.github.matches:
                        #print(" uploading match:",match_id)
                        upload_response = self.master.github.upload_content('matches/'+match_id, self.master.lex.base64_encode(self.master.lex.read_file(self.master.matches_path+match_id)))
                        if upload_response.get('content'): self.master.github.matches.append(match_id)
                match_details = self.master.lex.read_json(path=self.master.matches_path+match_id)
                player_count = 0
                for puuid in match_details['players']:
                    upload_response = {}
                    player_count += 1
                    backup_data = self.get_backup_data(puuid)
                    if not 'matches' in backup_data: backup_data.update({"matches":[]})
                    if not match_id in backup_data['matches']:
                        backup_data['matches'].append(match_id)
                    if not 'reports' in backup_data: backup_data.update({"reports":[]})
                    self.master.lex.save_file(self.master.json.dumps(backup_data, indent=4), self.master.accounts_path+puuid)
                    self.upload_backup_data(puuid, self.master.json.dumps(backup_data, indent=4))

                    print(" "*len(text), end="\r")
                    text = " Uploading Match Data to Github [{}:{}][{}:{}]".format(match_count,len(match_history),player_count,len(match_details['players']))
                    print(text, end="\r")

            #print(" "*len(text), end="\r")
            #text = " Uploading Match Data to Github [{}:{}]".format(match_count,len(match_history))
            #print(text, end="\r")
        print("")
        if match_found:
            match_found.reverse()
            self.master.match_history = match_found
        exit()

    def match_info(self, data):
        match_hold = {}
        if data:
            if data.get("ID"):
                match_hold.update({'id':data['ID']})
            elif data.get('MatchID'):
                match_hold.update({'id':data['MatchID']})
            elif data.get("matchInfo"):
                match_hold.update({
                    "id":data['matchInfo'].get("matchId"),
                    "map":data['matchInfo'].get("mapId"),
                    "server":data['matchInfo'].get("gamePodId"),
                    "queue_id":data['matchInfo'].get("queueID"),
                    "season_id":data['matchInfo'].get("seasonId")
                    })
                if data['matchInfo'].get("gameStartMillis") and data['matchInfo'].get("gameLengthMillis"):
                    game_time = (data['matchInfo']["gameStartMillis"] + data['matchInfo']["gameLengthMillis"])//1000
                    match_hold.update({"game_time":game_time})
            if data.get('MapID'):
                match_hold.update({'map':data['MapID']})
            if data.get('GamePodID'):
                match_hold.update({'server':data['GamePodID']})
            if data.get('QueueID'):
                match_hold.update({'queue_id':data['QueueID']})
            elif data.get('MatchmakingData'):
                if data['MatchmakingData'].get('QueueID'):
                    match_hold.update({'queue_id':data['MatchmakingData']['QueueID']})
            match_hold.update({'players':{}})
            if data.get('AllyTeam'):
                team_id = data['AllyTeam'].get('TeamID')
                if data['AllyTeam'].get('Players'):
                    for player_data in data['AllyTeam']['Players']:
                        if player_data['CharacterSelectionState'] == 'locked':
                            agent_id = player_data['CharacterID']
                        else: agent_id = None
                        match_hold['players'].update({player_data['Subject']:{
                            'team':team_id,
                            'agent':agent_id,
                            'rank':player_data['CompetitiveTier'],
                            'level':player_data['PlayerIdentity']['AccountLevel']
                        }})
            elif data.get('Players'):
                for player_data in data['Players']:
                    match_hold['players'].update({player_data['Subject']:{
                        'team':player_data['TeamID'],
                        'agent':player_data['CharacterID'],
                        'level':player_data['PlayerIdentity']['AccountLevel']
                    }})
            elif data.get("players"):
                data['players'].sort(key=lambda d: (d['teamId']).lower())
                for player_data in data['players']:
                    match_hold['players'].update({
                        player_data['subject']:{
                            "name":player_data['gameName'],
                            "tag":player_data['tagLine'],
                            "team":player_data['teamId'],
                            "party":player_data['partyId'],
                            "agent":player_data['characterId'],
                            "rank":player_data['competitiveTier'],
                            "level":player_data['accountLevel']
                        }})
                    if player_data.get('stats'):
                        match_hold['players'][player_data['subject']]['stats'] = {
                            "kills":player_data['stats']['kills'],
                            "deaths":player_data['stats']['deaths'],
                            "assists":player_data['stats']['assists']
                            }
            if data.get('PhaseTimeRemainingNS'):
                match_hold.update({'phase_time_remaining':data['PhaseTimeRemainingNS']//1000000000})
            if data.get("teams"):
                match_hold.update({"teams":{}})
                for teams_data in data['teams']:
                    match_hold['teams'].update({teams_data['teamId']:{"won":teams_data['won'],"score":teams_data['roundsWon']}})
        return match_hold




























#
