from configparser import ConfigParser

def load_config(filename='db.ini', section="postgresql")->str:
    parser = ConfigParser()
    parser.read(filename)

    config={}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in {1} file.'.format(section, filename))
    
    db_url = (
            f"postgresql://{config['user']}:{config['password']}@"
            f"{config['host']}:{config['port']}/"
            f"{config['database']}"
        )

    return db_url