from symtable import Class

from bot.utils.en import Messages as En
from bot.utils.fa import Messages as Fa


languages = {
    'en': En,
    'fa': Fa
}

def messages(language:str = 'en', admin_mode:bool =False):

    if not admin_mode:
        return languages[language]
    else:
        return languages[language]