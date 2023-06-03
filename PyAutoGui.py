# Exemplo de como usar o pyautogui
import pyautogui

pyautogui.PAUSE = 3
# abrir a ferramenta/o sistema/o programa

pyautogui.press("win")
pyautogui.write("login.xlsx")
pyautogui.press("backspace")
pyautogui.press("enter")

# preencher o login 
pyautogui.click(x=519, y=376)
pyautogui.write("Rapha")

# preencher a senha
pyautogui.click(x=488, y=428)
pyautogui.write("123456")

# clicar em fazer login
pyautogui.click(x=462, y=542)
pyautogui.press("enter")

import time

time.sleep(4)
# Verificar a posição do mouse
pyautogui.position()