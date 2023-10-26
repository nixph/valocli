base_url = "https://api.github.com"
api_version = "2022-11-28"
class Client:
    def __init__(self, master):
        self.master = master
        self.session = self.master.requests.Session()
        self.headers = self.get_headers()
        self.base_tree = self.get_tree()

        self.matches_sha = self.get_matches_sha()
        self.accounts_sha = self.get_accounts_sha()

    def hash(self, data):
        if isinstance(data, bytes): data = data.decode('utf-8')
        formula = "blob {}\0{}".format(len(data),data).encode('utf-8')
        return self.master.hashlib.sha1(formula).hexdigest()

    def request(self, path, data=None, method='get'):
        url = base_url+path

        if method.lower() == 'put':
            try:
                response = self.session.put(url, headers=self.headers, data=data)
            except Exception as e:
                print(" Error:",e)
                return {}
        else:
            try:
                response = self.session.get(url, headers=self.headers, data=data)
            except Exception as e:
                print(" Error:",e)
                return {}
        data = self.master.lex.read_json(content=response.content)
        if response.ok:
            if data:
                return data
            return response.content
        else:
            error_message = data.get('message')
            #if 'Not Found' in error_message:
            #    print(" Github account not found.")
        return {}

    def check_credentials(self):
        if self.master.config.get('github_user') and self.master.config.get('github_repo') and self.master.config.get('github_token'):
            return True
        else:
            print(" Need Github credentials in config file.")

    def get_content(self, path):
        if self.check_credentials():
            url = "/repos/{}/{}/contents/{}".format(self.master.config['github_user'], self.master.config['github_repo'], path)
            return self.request(url)
        return {}
    def upload_content(self, path, content, sha=None):
        data = '{"message":"%s","content":"%s","sha":"%s"}'%(int(self.master.time.time()), content, sha)
        if self.check_credentials():
            url = "/repos/{}/{}/contents/{}".format(self.master.config['github_user'], self.master.config['github_repo'], path)
            return self.request(url, data, 'put')
        return {}

    def get_tree(self, sha="main"):
        if self.check_credentials():
            url = "/repos/{}/{}/git/trees/{}".format(self.master.config['github_user'], self.master.config['github_repo'], sha)
            return self.request(url)
        return {}

    def get_accounts_sha(self):
        if not self.base_tree: self.base_tree = self.get_tree()
        if self.base_tree:
            accounts = {}
            for data in self.base_tree['tree']:
                if data['path'] == 'accounts' and data['type'] == 'tree':
                    tree = self.get_tree(data['sha'])
                    if tree.get('tree'):
                        for data in tree['tree']:
                            if data['type'] == 'blob':
                                accounts.update({data['path']:data['sha']})
            return accounts

    def get_matches_sha(self):
        if not self.base_tree: self.base_tree = self.get_tree()
        if self.base_tree:
            matches = {}
            for data in self.base_tree['tree']:
                if data['path'] == 'matches' and data['type'] == 'tree':
                    tree = self.get_tree(data['sha'])
                    if tree.get('tree'):
                        for data in tree['tree']:
                            if data['type'] == 'blob':
                                matches.update({data['path']:data['sha']})
            return matches

    def get_headers(self):
        headers = {}
        if self.master.config.get('github_token'):
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer "+self.master.config['github_token'],
                "X-GitHub-Api-Version": api_version
            }
        return headers































#
