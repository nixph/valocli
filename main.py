from lib import pylex, pyprocess, pyvalo, pyimport, pygithub, pyconstant
from lib.pykeyboard import readkey
from prettytable import PrettyTable
import datetime, pytz, timeago
table = PrettyTable()
table.field_names = ["", "=", "P", "Agent", "Name", "Rank", "Level", "Note"]


class PartyManager:
    def __init__(self):
        self.parties = {}
        self.party_colors = [(227, 67, 67),(216, 67, 227),(67, 70, 227),(67, 227, 208),(226, 237, 57),(212, 82, 207)]
    def get(self, party_id, retry=False):
        if party_id in self.parties:
            return self.parties[party_id]['color']
        else:
            self.add(party_id)
            if not retry:
                self.get(party_id, True)
    def add(self, party_id):
        if not party_id in self.parties:
            self.parties.update({party_id:{'count':1,'color':None}})
        else:
            self.parties[party_id].update({'count':self.parties[party_id]['count']+1})
        for pid in self.parties:
            if self.parties[pid]['count'] > 1:
                if not self.parties[pid]['color']:
                    self.parties[pid]['color'] = self.party_colors[0]
                    self.party_colors.pop(0)
    def clear(self):
        self.parties = {}
        self.party_colors = [(227, 67, 67),(216, 67, 227),(67, 70, 227),(67, 227, 208),(226, 237, 57),(212, 82, 207)]
party = PartyManager()

class Main:
    def __init__(self):
        pyimport.Import(self)
        self.lex = pylex.Lexicon(self)
        self.valo = pyvalo.LocalClient(self)
        self.github = pygithub.Client(self)
        self.process = pyprocess.Main(self)
        self.connected = False
        self.match_history = []
        self.match_history_count = 0

    def run(self):
        is_debug = False
        select_count = 0
        select_count_hold = None
        session_state = None
        session_state_hold = None
        match_info = {}
        match_id_hold = None
        match_dump_hold = None
        while True:
            if not self.connected: session = self.process.session()
            #print(self.match_history)
            #exit()
            if self.connected:
                presences = self.process.presences()
                #print(presences)
                #exit()
                if session['puuid'] in presences: session_state = presences[session['puuid']].get('session_state')

                if self.match_history_count == 0:
                    # LIVE MATCH
                    match_id, session_state = self.valo.get_match_id(session['puuid'], session_state)
                    if match_id:
                        if not match_id == match_id_hold or not session_state == session_state_hold:
                            match_id_hold = match_id
                            session_state_hold = session_state
                            match_info = {}
                            self.process.match_history(session['puuid'])
                        if not match_info:
                            match_info = self.process.match_info(self.valo.get_match_info(match_id, session_state))
                    else:
                        if is_debug:
                            match_info = self.lex.read_json(path="INGAME.json")
                            match_id = match_info.get("id")
                        if not session_state == session_state_hold:
                            session_state_hold = session_state
                            self.process.match_history(session['puuid'])

                else:
                    # RECENT MATCH
                    match_id = self.match_history[self.match_history_count-1]
                    if not match_id == match_id_hold:
                        match_id_hold = match_id
                        match_info = self.lex.read_json(path=self.matches_path+match_id)
                        table.title = "RECENT GAME: #{}".format(self.match_history_count)


            # GET PLAYER DATA
            if self.connected and match_info.get('players'):
                party.clear()
                text = " Downloading Players Data [{}:{}]".format(0,len(match_info['players']))
                print(text, end="\r")
                count = 0
                for puuid in match_info['players']:
                    count += 1
                    backup_data = self.process.get_backup_data(puuid)
                    if not 'matches' in backup_data: backup_data.update({"matches":{}})
                    if not 'reports' in backup_data: backup_data.update({"reports":[]})
                    if isinstance(backup_data.get('matches'), list): backup_data['matches'] = self.process.matches_fix(backup_data['matches'])
                    if session_state == 'INGAME' and match_info.get('id') and self.config.get('season_id'):
                        if not match_info['id'] in backup_data['matches']:
                            backup_data['matches'].update({match_info['id']:self.config['season_id']})
                    if puuid in presences:
                        if not match_info['players'][puuid].get("name") or not match_info['players'][puuid].get("tag"):
                            match_info['players'][puuid].update({"name":presences[puuid]['name']})
                            match_info['players'][puuid].update({"tag":presences[puuid]['tag']})
                        if match_info['players'][puuid].get("rank") == None:
                            match_info['players'][puuid].update({"rank":presences[puuid]['rank']})
                        if not match_info['players'][puuid].get("party"):
                            match_info['players'][puuid].update({"party":presences[puuid]['party']})
                        if not match_info['players'][puuid].get("level"):
                            match_info['players'][puuid].update({"level":presences[puuid]['level']})
                        backup_data.update({"name":presences[puuid]['name'],"tag":presences[puuid]['tag']})

                    if match_info['players'][puuid].get("party"): party.add(match_info['players'][puuid]['party'])
                    if not match_info['players'][puuid].get("note"): match_info['players'][puuid]['note'] = backup_data.get('note')

                    # GET DATA FROM 3RD PARTY
                    if not match_info['players'][puuid].get("name") or not match_info['players'][puuid].get("tag"):
                        name_tag_response = self.valo.get_name_tag(puuid)
                        if name_tag_response:
                            match_info['players'][puuid].update({"name":name_tag_response[0],"tag":name_tag_response[1]})
                            backup_data.update({"name":name_tag_response[0],"tag":name_tag_response[1]})

                    if match_info['players'][puuid].get("rank") == None:
                        mmr_response = self.valo.get_mmr(puuid)
                        if mmr_response:
                            match_info['players'][puuid].update({"rank":mmr_response[0],"rating":mmr_response[1]})
                            backup_data.update({"rank":mmr_response[0],"rating":mmr_response[1]})

                    # GET DATA FROM BACKUP
                    if not match_info['players'][puuid].get("name") or not match_info['players'][puuid].get("tag"):
                        if backup_data.get('name') and backup_data.get('tag'):
                            match_info['players'][puuid].update({"name":backup_data['name'],"tag":backup_data['tag']})
                    if match_info['players'][puuid].get("rank") == None:
                        if not backup_data.get('rank') == None:
                            match_info['players'][puuid].update({"rank":backup_data['rank']})

                    self.lex.save_file(self.json.dumps(backup_data, indent=4), self.accounts_path+puuid)
                    self.process.upload_backup_data(puuid, self.json.dumps(backup_data, indent=4))

                    print(" "*len(text), end="\r")
                    text = " Downloading Players Data [{}:{}]".format(count,len(match_info['players']))
                    print(text, end="\r")
                print("")
                if not is_debug:
                    self.lex.save_file(self.json.dumps(match_info, indent=4), session_state+".json")

            #    exit()
            #exit()
            if self.connected:
                while True:
                    match_dump = self.json.dumps(match_info)
                    if not match_dump == match_dump_hold or not select_count == select_count_hold:
                        match_dump_hold = match_dump
                        select_count_hold = select_count
                        print(" setting up table")
                        table.clear_rows()

                        if match_info.get('players'):
                            team_hold = None
                            count = 0
                            for puuid in match_info['players']:
                                if not team_hold == match_info['players'][puuid]['team']:
                                    if not team_hold == None:
                                        table.add_row(["", "", "", "", "", "", "", ""])
                                    team_hold = match_info['players'][puuid]['team']
                                count += 1

                                select_res = ''
                                if match_info['players'][puuid].get('selected'):
                                    select_res = self.color("■", fore="green", style='bright')

                                arrow_res = ''
                                if select_count == count:
                                    arrow_res = self.color(">", fore="green", style='bright')

                                party_res = ''
                                if match_info['players'][puuid].get('party'):
                                    party_color = party.get(match_info['players'][puuid]['party'])
                                    if party_color: party_res = self.color("■", fore=party_color, style='bright')

                                agent_res = ""
                                if match_info['players'][puuid].get('agent'):
                                    agent_uuid = match_info['players'][puuid]['agent'].lower()
                                    if agent_uuid in self.agents:
                                        agent_name = self.agents[agent_uuid].get("name")
                                        agent_res = self.color(agent_name, fore=self.agents[agent_uuid].get("color"), style='bright')
                                name_res = ''
                                if match_info['players'][puuid].get('name'):
                                    name_tag = match_info['players'][puuid]['name']+"#"+match_info['players'][puuid]['tag']
                                    name_res = self.color(name_tag, fore='white', style='bright')
                                    name_color = ""
                                    if puuid == session['puuid']:
                                        name_color = (221, 224, 41)
                                    elif match_info['players'][puuid].get("team") == "Red":
                                        name_color = (238, 77, 77)
                                    elif match_info['players'][puuid].get("team") == "Blue":
                                        name_color = (76, 151, 237)
                                    name_res = self.color(name_tag, fore=name_color, style='bright')
                                rank_res = ""
                                if not match_info['players'][puuid].get("rank") == None:
                                    tier = str(match_info['players'][puuid]['rank'])
                                    if self.ranks.get(tier):
                                        rank_res = self.color(self.ranks[tier].get("name"), fore=self.ranks[tier].get("color"), style='')
                                level_res = ""
                                if match_info['players'][puuid].get("level"):
                                    level = match_info['players'][puuid]['level']
                                    level_res = self.color(level, fore=pyconstant.level_to_color(level), style='')
                                note_res = ""
                                if match_info['players'][puuid].get("note"):
                                    note_res = match_info['players'][puuid]['note']

                                table.add_row([select_res, arrow_res, party_res, agent_res, name_res, rank_res, level_res, note_res])

                        self.os.system('cls')
                        print(table)
                        if match_info.get('players'):
                            if match_id and not match_id in self.match_history:
                                for id in self.match_history:
                                    if self.os.path.exists(self.matches_path+id):
                                        data = self.lex.read_json(path=self.matches_path+id)
                                        if data.get("players"):
                                            for puuid in match_info['players']:
                                                if not puuid == session['puuid']:
                                                    if puuid in data['players']:
                                                        if not "last_played" in match_info['players'][puuid]:
                                                            match_info['players'][puuid].update({"last_played":{"agent":None,"team":None,"time":0}})
                                                        if data['game_time'] > match_info['players'][puuid]['last_played']['time']:
                                                            match_info['players'][puuid]['last_played'].update({"agent":data['players'][puuid]['agent']})
                                                            if data['players'][puuid]['team'] == data['players'][session['puuid']]['team']:
                                                                match_info['players'][puuid]['last_played'].update({"team":"Ally"})
                                                            else:
                                                                match_info['players'][puuid]['last_played'].update({"team":"Enemy"})
                                                            match_info['players'][puuid]['last_played'].update({"time":data['game_time']})
                        if match_info.get('players'):
                            for puuid in match_info['players']:
                                if match_info['players'][puuid].get("last_played"):
                                    if match_info['players'][puuid]['team'] == match_info['players'][session['puuid']]['team']:
                                        team_res = self.color("(A)", fore="gray", style='bright')
                                    else:
                                        team_res = self.color("(E)", fore="gray", style='bright')
                                    if match_info['players'][puuid].get("agent"):
                                        agent_res = ""
                                        agent_uuid = match_info['players'][puuid]['agent'].lower()
                                        if agent_uuid in self.agents:
                                            agent_name = self.agents[agent_uuid].get("name")
                                            name_res = self.color(agent_name, fore=self.agents[agent_uuid].get("color"), style='bright')
                                    elif match_info['players'][puuid].get("name") and match_info['players'][puuid].get("tag"):
                                        name_tag = match_info['players'][puuid]['name']+"#"+match_info['players'][puuid]['tag']
                                        name_res = self.color(name_tag, fore="white", style='bright')
                                    else:
                                        name_res = self.color(puuid, fore="white", style='bright')


                                    played_text = self.color("played", fore="gray", style='bright')

                                    recent_team_res = self.color("({})".format(match_info['players'][puuid]['last_played']['team']), fore="gray", style='bright')
                                    recent_agent_res = ""
                                    recent_agent_uuid = match_info['players'][puuid]['last_played']['agent'].lower()
                                    if recent_agent_uuid in self.agents:
                                        recent_agent_name = self.agents[recent_agent_uuid].get("name")
                                        recent_agent_res = self.color("{}".format(recent_agent_name), fore=self.agents[recent_agent_uuid].get("color"), style='bright')

                                    new_local_time = pytz.timezone("UTC").localize(datetime.datetime.utcfromtimestamp(match_info['players'][puuid]['last_played']['time'])).astimezone(pytz.timezone("Asia/Manila")).replace(tzinfo=None)
                                    timeago_res = self.color(timeago.format(new_local_time, datetime.datetime.now()), fore="white", style='bright')
                                    print(" {}{} {} {} {}{}".format(team_res, name_res, played_text, timeago_res, recent_team_res, recent_agent_res))

                    key = readkey(True)
                    #log(" Key:",key)
                    if key == "esc":
                        exit()
                    elif key == "up":
                        if select_count > 0:
                            select_count -= 1
                        else:
                            if match_info.get('players'):
                                select_count = len(match_info['players'])
                    elif key == "down":
                        if match_info.get('players'):
                            if len(match_info['players']) > select_count:
                                select_count += 1
                            else:
                                select_count = 0
                    elif key == "left":
                        select_count = 0
                        if self.match_history_count == 0:
                            self.match_history_count = len(self.match_history)
                            break
                        else:
                            if self.match_history_count > 1:
                                self.match_history_count -= 1
                                break

                    elif key == "right":
                        select_count = 0
                        if not self.match_history_count == 0:
                            if len(self.match_history) > self.match_history_count:
                                self.match_history_count += 1
                            else:
                                match_info = {}
                                match_id_hold = None
                                table.title = "LIVE"
                                self.match_history_count = 0
                            break
                    elif key == "space":
                        if match_info.get('players'):
                            count = 0
                            for puuid in match_info['players']:
                                count += 1
                                if count == select_count:
                                    if match_info['players'][puuid].get("selected"):
                                        match_info['players'][puuid]['selected'] = False
                                    else:
                                        match_info['players'][puuid]['selected'] = True
                    elif key == "home":
                        pass
                    elif key == "end":
                        selected_puuid_list = []
                        if match_info.get('players'):
                            for puuid in match_info['players']:
                                if match_info['players'][puuid].get("selected"):
                                    selected_puuid_list.append(puuid)
                        if selected_puuid_list:
                            my_backup_data = self.process.get_backup_data(session['puuid'])
                            is_reported_triggered = False
                            for puuid in selected_puuid_list:
                                if not puuid == session['puuid'] or is_debug:
                                    backup_data = self.process.get_backup_data(puuid)
                                    if not 'reports' in backup_data: backup_data.update({'reports':[]})
                                    name_hold = ""
                                    if match_info['players'][puuid].get("name") and match_info['players'][puuid].get("tag"):
                                        name_hold = match_info['players'][puuid].get("name")+"#"+match_info['players'][puuid].get("tag")
                                    elif match_info['players'][puuid].get("agent"):
                                        agent_uuid = match_info['players'][puuid]['agent'].lower()
                                        if agent_uuid in self.agents:
                                            name_hold = self.agents[agent_uuid].get("name")
                                    else:
                                        name_hold = str(puuid)
                                    matches_found = []
                                    is_report_again = True
                                    for m_id in backup_data['matches']:
                                        if m_id in my_backup_data['matches']:
                                            if not m_id in backup_data['reports'] or is_report_again:
                                                matches_found.append(m_id)

                                    if matches_found:
                                        #print(puuid)
                                        report_success_count = 0
                                        report_failed_count = 0
                                        text = " Reporting: {} [{}:{}] [{}]".format(name_hold,self.color(report_success_count, fore="green", style='bright'),self.color(report_failed_count, fore="red", style='bright'),self.color(len(matches_found), fore="white", style='bright'))
                                        print(text, end="\r")
                                        for m_id in matches_found:
                                            if not m_id in self.reports_token: self.reports_token.update({m_id:{}})
                                            is_reported = False
                                            report_token_response = {}
                                            if self.reports_token[m_id].get(puuid):
                                                if self.reports_token[m_id][puuid]['expired'] > self.time.time():
                                                    report_token_response = self.reports_token[m_id][puuid]
                                            if not report_token_response:
                                                report_token_response = self.valo.get_report_token(m_id, puuid)
                                                self.time.sleep(.1)
                                            if report_token_response.get('Token'):
                                                if not report_token_response.get('expired'):
                                                    report_token_response.update({'expired':int(self.time.time()+3000)})
                                                    self.reports_token[m_id].update({puuid:report_token_response})
                                                    self.lex.save_file(self.json.dumps(self.reports_token, indent=4), self.reports_token_path)
                                                for i in range(0,3):
                                                    report_response = self.valo.report_player(puuid, report_token_response['Token'])
                                                    if report_response: is_reported = True; break
                                                    self.time.sleep(.1)
                                            if is_reported:
                                                report_success_count += 1
                                                if not m_id in backup_data['reports']: backup_data['reports'].append(m_id)
                                                is_reported_triggered = True
                                            else:
                                                report_failed_count += 1
                                            print(" "*len(text), end="\r")
                                            text = " Reporting: {} [{}:{}] [{}]".format(name_hold,self.color(report_success_count, fore="green", style='bright'),self.color(report_failed_count, fore="red", style='bright'),self.color(len(matches_found), fore="white", style='bright'))
                                            print(text, end="\r")
                                        print("")
                                    self.lex.save_file(self.json.dumps(backup_data, indent=4), self.accounts_path+puuid)
                                else: print(" u cannot report urself idiot.")
                                match_info['players'][puuid]['selected'] = False
                            if is_reported_triggered:
                                input("\n (Press Enter to Continue)")
                    elif key == "enter":
                        selected_puuid_list = []
                        if match_info.get('players'):
                            for puuid in match_info['players']:
                                if match_info['players'][puuid].get("selected"):
                                    selected_puuid_list.append(puuid)
                        if selected_puuid_list:
                            try:
                                note_input = input(self.color(" => ", fore="orange", style='bright'))
                            except KeyboardInterrupt:
                                note_input = None
                                print(self.color("================ ", fore="orange", style='bright'))
                            if not note_input == None:
                                for puuid in selected_puuid_list:
                                    backup_data = self.process.get_backup_data(puuid)
                                    backup_data.update({"note":note_input})

                                    self.lex.save_file(self.json.dumps(backup_data, indent=4), self.accounts_path+puuid)
                                    self.process.upload_backup_data(puuid, self.json.dumps(backup_data, indent=4))
                                    match_info['players'][puuid]['note'] = note_input
                                    match_info['players'][puuid]['selected'] = False
                        else: break






if '__main__' == __name__:
    app = Main()
    app.run()






















#
