TEAM_MAPPINGS = {
    # Оригинальное название: стандартизированное название
    'Union Berlin': '1. FC Union Berlin',
    'Wolfsburg': 'VfL Wolfsburg',
    'Bayern': 'FC Bayern München',
    'Bayern Munich': 'FC Bayern München',
    'Dortmund': 'Borussia Dortmund',
    'Leverkusen': 'Bayer 04 Leverkusen',
    'Leipzig': 'RB Leipzig',
    'Gladbach': 'Borussia Mönchengladbach',
    'Monchengladbach': 'Borussia Mönchengladbach',
    'Frankfurt': 'Eintracht Frankfurt',
    'Hoffenheim': 'TSG 1899 Hoffenheim',
    'Mainz': '1. FSV Mainz 05',
    'Köln': '1. FC Köln',
    'Bremen': 'SV Werder Bremen',
    'St. Pauli': 'FC St. Pauli',
    'Augsburg': 'FC Augsburg',
    'Kiel': 'Holstein Kiel',
    'Heidenheim': '1. FC Heidenheim 1846'
}

def normalize_team_name(team_name):
    """
    Нормализует название команды
    
    Args:
        team_name (str): Оригинальное название команды
    
    Returns:
        str: Стандартизированное название команды
    """
    return TEAM_MAPPINGS.get(team_name, team_name)