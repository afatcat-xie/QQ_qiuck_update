
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import win32gui, win32process, psutil
import random
import string
import threading
import time as _time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import keyboard
import os
import configparser
from datetime import datetime
from PIL import Image, ImageDraw
import pystray
import uiautomation as auto
import base64
import io

# ---------- 全局变量 ----------
running = False
worker_thread = None
time_interval = 0.1          
input_length = 10            
send_with_ctrl = False       
root = None                  
status_label = None
log_display = None  
tray_icon = None             
dictionary_files = []        
dictionary_pools = {}        
dictionary_enabled = {}      
enable_dictionary_mode = False

INI_FILE = "qq_config.ini"
LOG_DIR = "logs"

# Base64 编码的图标
ICON_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAKoAAACqCAYAAAA9dtSCAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAACHjSURBVHhe7Z0JeBRVtsdP9ZYVkhB2CIQlLAYFwvKEQRBFFBk2efr8UBzUQX0qi8vz4cMRcHQYhXFUXD6RUUZBQJGwKAoIgmyyCsoOYUlIWAIkBLL1Uvedc/s2hlhJupOq7qpO/b7vpOpWd1Wq7v33uUvdOiUxBExMdI5FLE1MdI0pVBNDYArVxBCYQjUxBKZQTQyBKVQTQ2AK1cQQmEI1MQSmUE0MgSlUE0NgCtXEEJj3+muA0+mEkpISbm63GzweD0iSBFarFRwOB0RFRUFERARPm9QMU6h+kJubC8eOHYODBw/CoUOH4MSJE5CTkwN5eXlw5coVKC0tBZfLBbIs/06ocXFx0KBBA0hKSoK2bdtCx44doUOHDtCyZUv+uYl/mEJVgMS3Y8cOWLt2LWzatIkLlMSqFuRlSbjdunWD2267Dfr16wft27cXn5ooYQpVQNX2xo0bYeHChbBq1So4efKk+ER7IiMjoXv37jBy5EgYMWIE97Ym11PrhXr58mX4/PPPYc6cObB7926xNXTUqVMHhg4dCk8++ST07t1bbDUBEmptBKt39uabb7Lk5GT6oerSBg8ezLDpIc64dlMrhbpgwQKWkpKiKA492gMPPMAyMjLE2ddOapVQsefOhgwZoigGvVt8fDx7++23xZXUPmqNUD/99FNWr149RREYyQYNGsQyMzPFVdUewl6oTqeTPfXUU4qFblRr2rQpW716tbjC2kFYCzU3N5cNGDBAsbCNblarlX3wwQfiSsOfsBXqyZMn2U033aRYyOFkU6dOFVcc3oSlUKnTZKRefU3txRdfFFcevoSdULOysliHDh0UCzSc7eWXXxY5EJ6ElVDz8/NZ9+7dFQuyNtg777wjciL8CKtbqMOHD4dly5aJVO2DZm7R9Q8ZMkRsCR/CZuL05MmTa7VICfI5Dz/8MBw+fFhsCR/CwqOuWLGCT+Qw8dKrVy9Yv349nxMbLhjeo549e5bPNFKbmJgYPt2uSZMmYou6aHn8rVu3AnauRCpMII9qZEaNGnVdh6KmRrOp3nvvPXbixAk+wyovL49hwbNHHnmEYRtQcZ9ArEWLFmzWrFns+PHj/PiXLl3ixx8zZozi96trFouFbdiwQeSS8TG0UNPT0xULqbpG99HpblZFLF++nE8OUdrXH7vrrrvYuXPnxNF+z5IlS1hsbKzivtWxtLQ0VlpaKo5ubAwr1KtXr6o6Xtq3b19WXFwsjl4xa9euZREREYrHqMz69+/v1/Gxvc1vjyodozo2c+ZMcWRjY1ihTp8+XbFgqmPkJY8ePSqOXDUzZsxQPE5F1qBBA35L11/oTpPScapj9evXZ6dPnxZHNi6GFGpOTg4vAKWCqY5NmTJFHNk/XC4X69Kli+KxlOytt94Se/oHtYupLat0rOrYxIkTxZGNiyGFOnnyZMUCqY7FxcWxU6dOiSP7z9y5cxWPV96SkpL4HbNAmTZtmuLxqmPU7qX5D0bGcEJV25sOHTpUHDkwLly4wBo3bqx4zLI2fvx4sUdg/Prrr8xutyseszo2YcIEcWRjYrhx1I8//hhQJCJVc+i5+qo4cOAArFu3jgec8JGYmOjXU6KDBg0Sa4FBz/mnpKSIVM359NNPITs7W6SMh6GEij19+OSTT0RKHTp37izWlJk0aRL/zu233w5paWk8IIUPugNUGRQl5cYbbxSpwEBvCjfccINI1Rz6kZFYjYqhhPrNN99ARkaGSNUcilhS2Z2hjz76CF5//XUeV4qgoBSjRo26FjWlKo/XtGlTHs6nLBSn6ttvv4WXXnoJHnnkEXjiiSfgjTfe4MEvfP/HR3JyslhTh3//+99QXFwsUgZDNAEMAQ2Y0ymrZXXr1uXzV5VA0VTYs/f14jdv3qz4uc9uueUW/j0fNEaampqq+F0ymqK4b98+8W3GXnvtNcXv1cToHIyIYTwqzQiiiRZqQ1PjlDh9+jQPjKbEli1b+JJC8VS0P1E2CNq7777Lp9/t37+fp6mNS/GnKDKKj507d0J6erpIacO8efPEmrEwjFCXL1/Oq001oQh8FVWFFKGvfFXsg4KoEbQ//tj5uhIUlpL44YcfYNy4cXy9b9++vAlDgddItOhBebub2r9U1dOcWh8FBQViTT2+//57PpHHaBhGqEuXLhVr6kEiPX/+vEhdD7Ut4+PjRep6yBMSVY0+XLp0iS99/+O5556DDRs2wN13382PT960RYsWMGbMGD7jae/evdCpUyf+XSIzM1OsqcfFixd5lEKjYQihUkzSXbt2iZS60LGVSEhIgDvuuEOkrsc397WipoGPM2fOcDHfe++98PPPP8PMmTPFJ7+H5o5im1mkgMdarejcaoohJ5h7m6r6hqbd0alqYTS9riLo/n/5Qf37779ffOrfFEPszYtvBwbFmoqJiVE8Zk2tSZMmDD2r+E/GwBAedfXq1WJNfWggv6K2IEWIpjYdipMP7k+dOvXaOC61U7HXz9cro7rnTvsVFhaKlLqQp9eqhtIMIVjdQhOLKYQNnapWhj1h8d/856uvvlI8Vnnr2LEjw06g2Ms/sNpnPXv2VDyeWma0WAC6FypVnUoZraZ17tw54AnGffr0UTyWkqEXFnv5x8KFCxWPo6aVH+PVO7oXKk38VcpotS2Q0DizZ89WPEZFRo+3YM9f7F059ARAMIILJyYmsrNnz4r/qn90L1TsMStmtNpGz0PNnz9f/NeKoQjQ1XlchKJH0zzWyqAnAAYOHKi4vxb2ww8/iP+sf3QtVKqOqY2nlMlaGD0C8o9//IO3EZVYvHgxS0hIUNzXH7vzzjsrnPt65MgR1q9fP8X9tDIKDW8UdP1cP00CodlHNGsqmGBHBh588EHo0qULn8V09OhRWLRoEb+jVFPq168PDz30EAwYMICv080AmqTy2WefaXInqjLoPGiiihHQtVDpDgoVqIk20A9y27ZtIqVvdD2OitWhWDPRgqysrGu3efWOKdRaDN33N8oEFV1X/aGMzhcdARAfI0H9ugAN4iRu9esA1KsjQRxurxPl/U6kQwK7FcCG5pvwJ2OOujwATheDYifA1WKAgmIG+djUvniFQS42RXMvM7hQwDANcLmQgUcWOwcZekvhwIEDRUq/6FaodFo9evTQ/FafwwbQvL4E7ZtJcEOSBTokSdCmsQRN6kmQiKKMjQSIsGPVQy+ILj/1tGzOlV0v/73yaRSlyw1cxCTS85cBMnMZHMmW4WAWgwNox8+SiLUvGnqK4c9//rNI6RfdCpV6+jTl7dSpU2KLeqQ0laDPDRbom2qBrm0skNyAvCR+4HtbOQqJoZFnJCMRqp1JNN+a9GvBPxZqgJHRBvxHNI31PHrcQ6cZbD0kw/pfZdh1TIbLRfi5ytD8hSlTpoiUftGtUOk146mpqZCfny+21Iz6dSW49w8WuLePFbqhOOvG4kYUBsMq2oPGBakTSMQkYP6afxSwjN731HkGa/bIMO8HD2w8oF474bHHHoMPP/xQpPSLbjtTNKZYVFRzF0IFPmGIDXa/5YD3n7ZD/5ssvG1JXstZ6q2C9SRSglwHtVmdLu850g+pZUMJHrvbCutec8A3UxzQqSW535qj5uvdtUS3QqW3Pvse5agJMx62w1tP2qBZosQLnQpfb8KsCjpdN3XO8Pxp/e6eFlj7qgM6Ynu6ppSNVaBndO1R1aAhPU2C5SmrV1uGFN5Qw2upGyVxqyk0r5aeJtA7uhWqWrdNH3vXBdPnu8GJVTxFCq/koVHdQ0NgDmy2/JzB4M4pTth2pOYCo+ZVRQ8x6gndClWtQAk0BPR/n7mh7yQnLP9J5kI1mmB9As25yOB/5rihz/+Wwo/71fGC9GSvKdQaQI8rq8muDBmGveqEO/7ihK+3ybydSoVv1WkO0O+IxnjpHLNyGfzlUzd0e8YJM9PdUKRi1pBIPdRb0zm6FapWv3IakxzyVyf3sHO+8/BBdRKDw64PL2vDEvH9gHYcZfDUey5IQ4G+usjNx1bVhtqnplBrgNbDu9uxfTd2FopgohPGf+CCTViVUs/aJ1oa1goG9G941Y7NEfq/OXkM/oU/oDtedkLvF0rh/ZUeuKThHSrKZ50OpV+Hbgf858yZA2PHjhWp4NC5lQX+2MMCg7pZ4MaW2twUUBrMp9unmw7IsGK7DOt+kfkcgGDRvHlzHq2FIg/qGd0KlSb0UgSRUEG3WXt3sEC/ThZIa2uB5IYSxEXjByQwAvsylHPXjLb5chKFSJ7SJ0peb9ESP3dh5+4c3R7NYrDlkAwb9smwG3vx+YW+nYMLRWohoZaNgaVHdCvUzz//HB544AGRCi3UqUmiiSvNJUhNskA7XLZsIEHDeAniUbxR1FywSVyUlJnUhCh1MSgs8c6Wyr4IcPysDAdPMziQySDjrHfmlB5o3bo1F2rZgG56RLdC/SJ9CfzXPSNFSp+QgKMjJC7UCFznk0sQui1b4gLsnTPeQ9dnDntJbt8eDv3yC0To/HWUuu1MpV4phrslOzS2ogJ0Ct1EoCr7zCUGJ897p+aRZV1gfL4peVS9ijQC2yWpkhX+ZI8ChwHGUXXrUa/cOxrkHzdDLnaJ97lKYGtpMfyEdtBVCrmy/odT9IYDhdnSaoc0RyT0joiGHhGR0BrTUdhDjPx0NjgG9Bff1Ce6FKr7l32QN+Q/+RQiK2awDc2KvREnnup57CYfxh7JbmcJWjEcwPVsjwtK9Fy/hoB6Fiu0ttmhMwqzG9pN9khIxnRdbJ9Qv458qBvzTC4pgchhf4S6c97j++kVXQr16st/haL3PwKpXAPf14H2CdeDXZcCWeZCJfHuQ29LluF2Qg5WZ1dp9nOYQ4MQidg8Im/Z3u6AG+0RkIrWCtcbolgjMa8IEqaHhMlTZcD8k6KjIWH1MrC2UvedAWqiO6HK+fmQd/sfQc456x0JrwISLnld77CkhAXC4CpmPjUPstwuOIaiPYIiPo7LLI8bzqNdxs/pe0YiWrJwL9kERUmesa3NAW3tdvSaDmiG2xKuiVJCMTL0ljSCxvy6SlZcDLGTX4DoZ54WW/SH7oRa8sUSKHjqGZAiI8WWwCHxkmitWG7e3qLX+xahh80nEaNYz6Blo51GMdPyHDYpLng8+LmHe+JizBZqamgNnV8kijAaRVYXxVYPq+YGKDwSJAmwOXrKZjYbNLbYoJ7VCnXwu9QRousjIZKH9HnKap+tywXW9u0gYdUyzPcIsVFf6E6o+SMfAOfGLSBFqD9c4m06eMc7yQN7/c9vHqiUxIxCLkShUpOigHm49yUrQAEX4Hby1iT4Isy2UmHknemH4MFj0DF5uxqXdlySqKJQXFG4jMVlLAqxLi7jUJRxuE5LStP2GPE92s97fhIeVYgRTcb/RYWlRYExFGv8Z3PAcUfVL4gLBboSqnvPL5A39D7ebgr2DBHff6MliZn+vXe97GfeNV+F6hONLwN9S/pWWfPi3du3Z9l9uTcsI0KyYMN03qny1ow6oWTxUmD0nFSQRUqUFQ15SBcKh6p+Gk2gZgCZ15N6mwVk9Bl5VPoeGe3j24+2l923+Nq+3v3L7ku9b+4xxTmEAsnhAOeGTeA5cVJs0Re6Eap8KQ9KV67iGWYSArDpIedhGSz9WmzQF7oRqvO7NeDJOo0NvKp7+ibaIGGnrWTpCt4M0Bu6EWrJl+mYU7pqidQ+7HZwHzrKmwB6QxfKcP28F1w7d2O1bxdbTEKG7IGSRV+JhH7QhVBL0ZvSoHMoOlEm10N9BNfGzeDJOCG26IOQC1W+dAlKv11tdqL0Au9U5UNJ+nKxQR+E3qOuWgtwOsfsROkIC7ZV2bJvAIr106kKqVBp3PD7BQvhHPPwaWh0B4fuyuiiPVKLoAYXTfKhuQJUBm50Gtv274MDOnq5b0jvTB04cAC6pHWFOk4X9IyMgX4R0dArIopPuCg/HS1kJxmGUL5S7tpwhQRKNx7OeFywx1UKP5YUwpbSYj4LbfiIEZC+ZIl3pxATUqFSbM5p06aJlBcbZlxrrHq6O6LgDyhamujbwmqHOkK4dAeHz6Pk3zbxB+4x0VvS/APKxVImwzns3dMkdJqMTpPS9+N6Hm4rCz3w9+uvv0LLli3FltARMqFSJJS0tDTuVSuDJnW0stmhCwq2B4qXlq1QuAlYPdkx02lCiUuW+Qyiaw8t1WYoHzA/HFYbn7dL+UOTbLLdbi7Mnc4Sbodw/WI5YSrx1ltvwYQJE0QqdIRMqNV9NQ9JkabAtbdHQGdHBNxoi4Ae9epDU9zmyc8HRs//YAGRaCX0zGE75EXFRubxAKNgqihGumZLdDTICfGw49wZ2FNUCHtRkOQtT7ldXLCB0qtXL9iyZYtIhY6QCfXRRx+Fjz/+WKRqxt+mToMXn3wKnPv2g/vQEfAcOgzujBPgOXoMWGFoJrmogk+MMrbRyfvRrDJK4/XQcJ5Utw5YGjUCa3ILsLVLAVvH9mDv0A4K4+pCpz/0hsyTNZ9gYkHx79ixg9d+oSQkQqXXxlB8frVeHbPoiy/gvnvvFanfKPjviVCyOL1Gk7BVx5fdPhEKYxSGhTye73NRI0gx0SDFx4OlYQOwNm+GomwJ1jatuDitzZqCVD9RcQy6zy23wOZN6twKnTRpEkyfPl2kQkNIhLpgwQIYNWqUSNWcrVu3ws033yxSv1Ew/nkoWfClekLl1Sx6tjICqxr05uTRyalLKD56vMaGXUZqluB5kRAt6Bm5GFF0lsYNwdqkMVjIGqM1rA+WegkgBRjJhPKX8lkNOnToAHv27IGIiNDN/g+JUIcNGwbLl6tz5yMmJgZ++eUXHvGjPAXjnoOShYvVESoKNGbSc2BL7QgyRcMuKQVGodupTUyhUWgAzYIi9HlFWidRklfEAqZzkKKjvB4yNta7xPYkX9L5oXjVhLzg66+/LlI1Z926ddC/f+geqQ66UDMzM/mLeNUKfd6kSRPYv38/JCQkiC2/oapQXS6IWzwPHH16iw365p133lG1t/7kk0/Ce++FbvZ/0MdzvvvuO1XfohyPVSZ51aBAb6owCI2x2aAmK1euDPpbvssSdKGmp6eLNXUgoTrMCS2/IzExUaypA72SPpTDVEEVKlX7al+sUpVv4v0BSyoPyy0J4e3UoAp1/fr1qlb7hN7jeoaKWOywqV3TrFmzBgoLC0UquARVqN98841YUw9TqMpQvFO1hXr8+HHYuXOnSAWXoAmV3hC3ceNGkVKP6GgKA21SHhrztNNYrcpQpyoUBE2o27dvhzNnzoiUekSqMfQUhthsNk2EStV/KN70FzShrlq1SqypixaFEQ5YrVYuVrWhMevDhw+LVPAIilDpPUbUkdICLQojHKDJJCRWtaEXKf/4448iFTyCItRjx47BwYMHRcokGKg9NFUWmqIZbIIi1J9++om/c1MLjPDWuVBA7Uit2pLU36C3UgeToAhVy6rC5TLObc1gouWrI0+dOhX0GlJzodI7TekXqBVqv9w3XCCRavnWaKolg4nmQqV7xBkZGSKlPmq9Lj3coJpGS6HSHOBgorlQ6SlGLcUUqlt6eof6BFo2i/bu3ctHAIKF5kLdtWuXWNOGShv1fs/CDz/IOWjZLKJ2alZWlkhpj+ZCpUcYtOTy5cti7ffw1/9YLMCwwCgIGysu8a6TJ6D3QFJng4x6x0pGn2H1Sd9nJVjotM0g0OQfLT1qUVERHDp0SKS0R1OhUvVz9OhRkfIPGqhu1KiRSFXNpUuXKuzdxkz+H/6mj7jZsyD2L5Mg6pHREDFoINh7dANru7ZgadoELImJ/GnOa4+GkMXGeJ9hatwIrG1ag717GkQMGwyWZk3FkfUP5Yu/0N29Bg0aiJT/ULMuaNCjKFqBHSlWp04dqnv9tmHDhrHx48crfqZkzZs3Z+hVxX/0H7mkhMmXC5jn/HnmPp3N3CczmfvEKa9lZjHPmbPMcymPyUXF+GVZ7GUc5syZo5hfShYbG8tmz57NoqKiFD+vyEaPHi3+m/Zo6lGpDRPIwDA9UvLPf/4zII9Ks7Lo8etA4Q/c0XPx6EnosWNryyTvI8hkSc25N7UkxGPzIZJu84i9jANNUg+EoUOHwsSJE0XKP7QczSmPpkKlBncgUCyqVq1a8dnp/kK9/uzsbJEy8RGIiGiSNc1Ce/nllyE1NVVsrZqcnJygPUelG6Heeuut8Oyzz/L1Fi1a8KW/BNoOrg0EkicNGzbktRmJddasWX7PE6B2MNVowUBTofo7/5R+0ZRB1JEi6Bn9QKbvBbVRbwCoKRSIk6D89s1Co2f3n3/+eb5eFVSbVafZVR00FeqFCxfEWuVQuBgK8eMjKSmJP6/vLzT4bPIbVO2fO3dOpKqmc+fOYs3LK6+8At27dxepiqHRlrDwqP48yHfPPffA009f/1Zjeg6qrHCrgkJXBuuXbQQCfa6pZ8+eYs0LNQFmz57t12M+aj+sWRGaCrWqqX3Jycnw/vvvi9T19O3bV6xVDQVb27dvn0iZBPJsGj1u3qVLF5H6ja5du8KMGTNEqmK0mr5ZHk2Fyiq5fUltIgo7WdFQ1G233RbQ5F+tniAwGtQLD2RmU7du3aBpU+UbGRTGZ/To0SKlTGVlrCaaCrWy6G9vvPFGpUG36FceyFDJ6tWrxVrtZvfu3XzGmr8MGTJErClDNR6JuSKCFeFPU6HWq1dPrF3P448/Ds8884xIKUO9fhqE9hea/BLMe896ZcWKFWKtaqgNOnjwYJFShkZkKHxlRbGsghWpRlOhUhu0PCS+d999V6Qq57777vP74T2aKbRs2TKRqp1QezEQoVLzqk2bNiJVMSkpKfDFF19w0ZaFvGkgozM1gt9I1Yj09PTr7g3jr5cVFRWJT/1j4MCB1x2jMsPmAnO5XGLP2se3336rmC8VGZVPIGDz6rq5G23btmXFxcXiU23RVKh5eXmsVatW/KKwYc7Q64lP/Gfp0qXXMsYfo8ysrYwcOVIxT5SsU6dO1SoP7Kgx7DvwY7z00ktiq/ZoKlTiwIEDbPv27SIVOG63m6Wlpf0uoyuy4cOHiz1rF/v372dYFSvmiZLR7KrqUlBQwL7//nt29epVsUV7NBeqGmD7SDGzlcxisfBffW3jscceU8wPJevYsWPQqmy1MIRQib59+ypmupLdc889Yq/aAdVagcwlnTdvntjTOBhGqBs3bmSSJClmvJKtWbNG7Bn+3H///Yp5oGT9+/cXexkLwwiVoA6ZUuYrWbdu3arVWTAaK1euVLx+JXM4HGznzp1iT2NhKKFevHiRtWnTRrEQlOyVV14Re4Yn9AhOhw4dFK9dyaZMmSL2NB6GEipBw09KhaBk5EE2b94s9gw/nnjiCcXrVrI+ffowp9Mp9jQehhMqQZ5BqTCUrF27diw3N1fsGT7MnTtX8XqVLDExkR0+fFjsaUwMKVRixIgRioWiZIMGDeLjseHCpk2bWHR0tOK1KhndNDE6hhVqfn4+6969u2LBKNmYMWPEnsaGBvYbN26seI1K9uabb4o9jY1hhUqcOnWK329WKiAlGzt2rNjTmBw8ePDaLWl/7IUXXhB7Gh9DC5U4cuRIQIVHQROMOGy1bds21qxZM8VrUrIJEyaIPcMDwwuVILGmpKQoFpiS0aB3dna22Fv/LFq0KKCIM88++6zYM3wIC6ESmdm5rEePHooFp2QtWrTgg+V6hu7HP/fcc4rnX5G9+tp0sXd4YXyhym7mubgN3epUdnFZJ3bPzcoFWJE9/fTT7MKFC+Jg+mHDhg2sa9euiuesZNERwD6ZGMnYrpFMPjWXyUWnxZHCg6C/r18tWPFpkE9/ifYFsPw9wNwlYHfYQGY2+NuXbpi2wI3r4stVQJFZJk+eDA899FDIX7BGEU4ozsHcuXPJiYitldMxSYJ/jbNDr1QLOItLvNKNbASWhreDpcWDfAkWY7+B23BCJVF6jn8Ick46QMk5vAILFgJFVfE+sWrBhQ3LZPVOGcZ96IIjOf5fHj1MOG7cOP4ITLDfWk3RXuhBus8++yygKNqPDLDC38fYoUE8vQNKbCQYxX11YbZYQYrvApZWj4IVRQs2Y7471jBCZVcOg+fwdPSgiwHcWJAkTiyEiqD31ebmA7yy0AUfrPSAJ4AYvNi75oExSLAUMUQrL0vxCOiVjfPnz4d169YFFHi3bRMJ/v4nO4z8g4XHF3Yrh4hFsHhJsEwGqU4HsKSMB2vyo4bzsPoXKnoGz5EZKNIZ6DIueTOYvKgf2MjZ2gA27pNhynw3/PBr4BGj27VrB/369eNB3CgoAzUTKKBYoFA25+bm8qqdXtRAwty2bVtAAXeJOlEATw+2wbPDbVAfvagLvajfBcgF6wEpsTfYbpqJy17iA/2jb6GiMN07/oTV/NcA1so9aGU4cFeKhL70Jw+8scQDO49WL8Q5vVacvC09XUvhMSlGFgXQoDCZvteO0/ud6IlYCgRBYYYoNCMFLDtx4gRf+huPqzzYWYJR/axcoB1bSuBBzQVSS1yHB9uxtliwolitrR8XG/WNjoXKwL11JFb12Ba11bzqpaArFCCQItB8je3XD1a6YT16WH87XKGiYZwE9/e1wtg7rdApWaIanP/oagy1YfFgtl6LwdJ0uNioX3QrVPncanBvuku0pfwP7VMVPsF6sLB3oGedv94Dy7fLkJmrn2ywY3OlZ4qFe9Bh/2GBZg1RoKgrVQRaFrkEpHo3g/3WTZgx6r/gV010K1TP0bfBs2eiKt5UCS5Yim2B7diL2OnafFCGFds9sAHbsxlnWNA9bd1ogM6tLHBXmgXu7maFVKze7fgbrVEVXxWkfkci2O/YC1JEQ7FRn+jXo+auB/fGO3AF3Qjv4VMHSj3PWhYrHtoqArIUFAIczJJh22EGPx2RYd9Jr7e9XOT9XA1s6LyoSqeee1obC/Tu6F22RM9pw0sF8p5UM2tVMtR+IJF6sGPVqB/Y+67FrDU9arWRz6wA+cQckPP3AJSex4xVCHHII/4Juxb9r7ygy6bLX26ZNGYFBb22WXCbFQ3Ls6iEwbk8QLECnDgHcBItGzvq59AL56Oor5Riu9dtBzdEA6MxSuxZW+Qr4JBKINohQ12sEBJxc5MEgBYNAJIbAbRCa5bo3W514LkxCWTSjYxVPJ1OhddB+HEt/CDCyhcv/eDxPKXolmBpNAAsKRNBikoSH+oXXQv1Gs6LwApPoGUAK8oEKM4BVorKceUBc13BEkZ35ylGkdBYDXpgNMa9BtWZtCxziT7PgQUm0ToVnITulIw8N7WJLdjFRpOskbg5GsUUg1VkLFpdbC+g2eLQ4vE78eCxxIHbmsCXYMPPmAskdz7Y5Mtg8+SBJKOiPZfRcOkqwGshuwLMWYjVeiE6Njxv+gHK9MI1Mqzr+TASXYfHex38GpSuRdQyeB3ea0Hj14C/DmsUnk8MSHY8L0c9rNrx1xGdhAJNBim2NRcqv06DYAyhVsW1gkWjpgIXKrqoawVcFhImeSWfUH0FjAZl0lwEQYTO9zrzCZXW6RqwmHzLa4hrufajoyYS/eDED4+2hQnhIVSTsCfIbsPEpHqYQjUxBKZQTQyBKVQTQ2AK1cQQmEI1MQSmUE0MgSlUE0NgCtXEEJhCNTEEplBNDADA/wMSxpqg7KDHYAAAAABJRU5ErkJggg=="

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日志初始化
log_filename = f"qq_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
LOG_FILE = os.path.join(LOG_DIR, log_filename)
log_fp = open(LOG_FILE, "a", encoding="utf-8")

def log_info(message):
    """线程安全的日志记录，支持文件、GUI和控制台输出"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    
    if log_fp:
        log_fp.write(f"[{full_timestamp}] [LOG] {message}\n")
        log_fp.flush()
    
    if log_display and root:
        try:
            # 直接更新 UI，而不是使用 after 延迟
            log_display.insert(tk.END, formatted_message + "\n")
            log_display.see(tk.END)
            root.update_idletasks()  # 立即处理待处理事件，确保日志及时显示
        except: pass
    print(formatted_message)

def update_status(text, color):
    """更新 GUI 上的状态标签"""
    if root and status_label:
        root.after(0, lambda: status_label.config(text=f"状态: {text}", fg=color))

# ---------- 核心检测与自动发送逻辑 ----------
def active_window_process_name():
    try:
        pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
        return(psutil.Process(pid[-1]).name())
    except:
        pass
def worker_logic():
    global running
    # 仅允许 EditControl，排除了可能导致死循环或误触发的 DocumentControl
    VALID_CONTROL_TYPES = ['EditControl']
    
    with auto.UIAutomationInitializerInThread(debug=False):
        log_info("核心监控引擎已启动...")
        while running:
            try:
                # 先检查焦点窗口进程名是否为 QQ.exe
                process_name = active_window_process_name()
                
                if process_name != "QQ.exe":
                    update_status("非 QQ 窗口", "orange")
                else:
                    el = auto.GetFocusedControl()
                    
                    if not el:
                        update_status("等待有效焦点", "orange")
                    else:
                        ctrl_type = el.ControlTypeName
                        window = el.GetTopLevelControl()
                        win_title = window.Name if window else "未知窗口"

                        print(f"焦点窗口: [{win_title}] | 进程: {process_name} | 控件: [{ctrl_type}]")
                        
                        # 明确禁止在文档展示区（通常是聊天记录区）尝试输入
                        if ctrl_type == 'DocumentControl':
                            update_status("禁止在文档区输入", "red")
                        elif ctrl_type in VALID_CONTROL_TYPES:
                            # 模拟输入逻辑
                            text_to_send = get_random_from_dictionaries()
                            if text_to_send is None:
                                text_to_send = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(input_length))
                            keyboard.write(text_to_send)
                            _time.sleep(0.1) # 缓冲，防止发送过快
                            
                            if send_with_ctrl:
                                keyboard.press_and_release('ctrl+enter')
                                print('ctrl+enter')
                            else:
                                keyboard.press_and_release('enter')
                                print('enter')
                            
                            log_info(f"【发送成功】窗口: {win_title} | 内容: {text_to_send}")
                            update_status("运行中 (发送成功)", "green")
                        else:
                            update_status("无效输入区域", "orange")

            except Exception as e:
                log_info(f"【循环异常】: {str(e)}")
            
            _time.sleep(max(0.1, time_interval))
        log_info("核心监控引擎已安全停止。")

# ---------- 托盘与配置功能 ----------

def create_dummy_icon():
    """从 base64 创建托盘图标，失败则创建备用图标"""
    try:
        image_data = base64.b64decode(ICON_BASE64)
        return Image.open(io.BytesIO(image_data)).convert('RGBA')
    except:
        # 创建备用图标
        image = Image.new('RGB', (64, 64), color=(0, 120, 215))
        ImageDraw.Draw(image).rectangle([16, 16, 48, 48], fill=(255, 255, 255))
        return image

def on_tray_quit(icon, item):
    icon.stop()
    if log_fp: log_fp.close()
    root.after(0, root.destroy)

def show_window(icon, item):
    icon.stop()
    root.after(0, root.deiconify)

def withdraw_window():
    """点击窗口关闭按钮时隐藏到托盘"""
    root.withdraw()
    global tray_icon
    image = create_dummy_icon()
    
    menu = (
        pystray.MenuItem('显示窗口', show_window), 
        pystray.MenuItem('退出程序', on_tray_quit)
    )
    tray_icon = pystray.Icon("QQTool", image, "QQ自动发送工具", menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()

def load_dictionary(filepath):
    """加载UTF-8格式的字典文件，支持多个字典"""
    global dictionary_files, dictionary_pools, dictionary_enabled
    try:
        # 检查是否已加载
        if filepath in dictionary_files:
            log_info(f"字典已存在: {filepath}")
            return False
        
        with open(filepath, 'r', encoding='utf-8') as f:
            word_list = [line.strip() for line in f.readlines() if line.strip()]
        
        if not word_list:
            log_info(f"字典文件为空: {filepath}")
            return False
        
        dictionary_files.append(filepath)
        dictionary_pools[filepath] = word_list
        dictionary_enabled[filepath] = True  # 默认启用新加载的字典
        log_info(f"字典已加载: {filepath} ({len(word_list)} 条记录)")
        return True
    except Exception as e:
        log_info(f"加载字典失败: {str(e)}")
        return False

def remove_dictionary(filepath):
    """删除加载的字典"""
    global dictionary_files, dictionary_pools
    if filepath in dictionary_files:
        dictionary_files.remove(filepath)
        del dictionary_pools[filepath]
        log_info(f"字典已删除: {filepath}")
        return True
    return False

def get_random_from_dictionaries():
    """从所有启用的字典中随机抽取一条"""
    if not enable_dictionary_mode or not dictionary_files:
        return None
    
    all_words = []
    for filepath in dictionary_files:
        if dictionary_enabled.get(filepath, True):  # 只从启用的字典中选择
            all_words.extend(dictionary_pools[filepath])
    
    return random.choice(all_words) if all_words else None

def load_config():
    global time_interval, send_with_ctrl, input_length, enable_dictionary_mode, dictionary_files, dictionary_enabled
    config = configparser.ConfigParser()
    if os.path.exists(INI_FILE):
        try:
            config.read(INI_FILE)
            if 'Settings' in config:
                time_interval = config.getfloat('Settings', 'interval', fallback=1.0)
                input_length = config.getint('Settings', 'input_length', fallback=10)
                send_with_ctrl = config.getboolean('Settings', 'send_with_ctrl', fallback=False)
                enable_dictionary_mode = config.getboolean('Settings', 'enable_dictionary_mode', fallback=False)
                
                dict_files_str = config.get('Settings', 'dictionary_files', fallback="")
                if dict_files_str:
                    for filepath in dict_files_str.split(';'):
                        filepath = filepath.strip()
                        if filepath and os.path.exists(filepath):
                            load_dictionary(filepath)
                
                # 加载启用状态
                dict_enabled_str = config.get('Settings', 'dictionary_enabled', fallback="")
                if dict_enabled_str:
                    for item in dict_enabled_str.split(';'):
                        item = item.strip()
                        if '=' in item:
                            fpath, enabled = item.split('=', 1)
                            fpath = fpath.strip()
                            if fpath in dictionary_enabled:
                                dictionary_enabled[fpath] = enabled.lower() == 'true'
        except: pass

def save_config():
    global time_interval, input_length, send_with_ctrl, enable_dictionary_mode, dictionary_files, dictionary_enabled
    config = configparser.ConfigParser()
    
    # 生成启用状态字符串
    enabled_str = ';'.join([f"{fpath}={dictionary_enabled.get(fpath, True)}" for fpath in dictionary_files])
    
    config['Settings'] = {
        'interval': str(time_interval),
        'input_length': str(input_length),
        'send_with_ctrl': str(send_with_ctrl),
        'enable_dictionary_mode': str(enable_dictionary_mode),
        'dictionary_files': ';'.join(dictionary_files),
        'dictionary_enabled': enabled_str
    }
    try:
        with open(INI_FILE, 'w') as f:
            config.write(f)
        log_info(f"配置已保存到 {INI_FILE}")
    except Exception as e:
        log_info(f"保存配置失败: {str(e)}")

def toggle_worker():
    """切换监控开启/关闭状态"""
    global running, worker_thread
    if running:
        running = False
        update_status("已停止", "blue")
        log_info("已停止监控")
    else:
        running = True
        worker_thread = threading.Thread(target=worker_logic, daemon=True)
        worker_thread.start()
        update_status("运行中", "green")
        log_info("已启动监控")

def start_worker():
    """启动监控"""
    global running, worker_thread
    if not running:
        running = True
        worker_thread = threading.Thread(target=worker_logic, daemon=True)
        worker_thread.start()
        update_status("运行中", "green")
        log_info("已启动监控")

def stop_worker():
    """停止监控"""
    global running
    if running:
        running = False
        update_status("已停止", "blue")
        log_info("已停止监控")

def clear_logs():
    if log_display:
        log_display.delete('1.0', tk.END)
        log_info("日志界面已清空")

# ---------- GUI 界面构建 ----------

def run_gui():
    global root, status_label, log_display
    load_config()
    
    root = tk.Tk()
    root.title("QQ 自动发送监控工具")
    root.geometry("700x1000")
    root.protocol('WM_DELETE_WINDOW', withdraw_window)

    # 样式配置
    style = ttk.Style()
    style.configure("TButton", padding=5)

    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 配置行权重，使行8和行15能够扩展
    main_frame.rowconfigure(8, weight=1)
    main_frame.rowconfigure(15, weight=1)

    # --- 设置区域 ---
    settings_label = ttk.Label(main_frame, text="参数设置", font=("微软雅黑", 10, "bold"))
    settings_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

    ttk.Label(main_frame, text="发送间隔 (秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
    interval_var = tk.DoubleVar(value=time_interval)
    ttk.Entry(main_frame, textvariable=interval_var, width=15).grid(row=1, column=1, sticky=tk.W)

    ttk.Label(main_frame, text="随机字符位数:").grid(row=2, column=0, sticky=tk.W, pady=5)
    length_var = tk.IntVar(value=input_length)
    ttk.Entry(main_frame, textvariable=length_var, width=15).grid(row=2, column=1, sticky=tk.W)

    send_method_var = tk.BooleanVar(value=send_with_ctrl)
    ttk.Checkbutton(main_frame, text="使用 Ctrl+Enter 发送 (QQ设置需匹配)", variable=send_method_var).grid(row=3, column=0, columnspan=2, pady=5, sticky=tk.W)

    # --- 字典设置 ---
    ttk.Separator(main_frame, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
    dict_mode_label = ttk.Label(main_frame, text="字典设置 (可选)", font=("微软雅黑", 9, "bold"))
    dict_mode_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=5)
    
    dict_enable_var = tk.BooleanVar(value=enable_dictionary_mode)
    def on_dict_mode_changed():
        global enable_dictionary_mode
        enable_dictionary_mode = dict_enable_var.get()
        if not enable_dictionary_mode:
            dict_list_label.config(text="字典列表: (已禁用)", foreground="gray")
    
    ttk.Checkbutton(main_frame, text="启用字典模式", variable=dict_enable_var, command=on_dict_mode_changed).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=5)
    
    dict_list_text = "字典列表: " + (f"({len(dictionary_files)} 个)" if dictionary_files else "(未加载)")
    dict_list_label = tk.Label(main_frame, text=dict_list_text, foreground="green" if dictionary_files else "gray", font=("微软雅黑", 9))
    dict_list_label.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=2)
    
    # 字典列表显示框
    dict_display_frame = ttk.Frame(main_frame)
    dict_display_frame.grid(row=8, column=0, columnspan=2, sticky=tk.NSEW, pady=(15, 5))
    
    # 创建Canvas和Scrollbar用于可滚动的字典列表
    dict_canvas = tk.Canvas(dict_display_frame, height=150, bg="#f5f5f5", highlightthickness=0)
    dict_scrollbar = ttk.Scrollbar(dict_display_frame, orient=tk.VERTICAL, command=dict_canvas.yview)
    dict_scrollable_frame = ttk.Frame(dict_canvas)
    
    dict_scrollable_frame.bind(
        "<Configure>",
        lambda e: dict_canvas.configure(scrollregion=dict_canvas.bbox("all"))
    )
    
    # 配置 dict_scrollable_frame 让其内容能占满宽度
    dict_scrollable_frame.columnconfigure(0, weight=1)
    
    dict_canvas.create_window((0, 0), window=dict_scrollable_frame, anchor="nw")
    dict_canvas.configure(yscrollcommand=dict_scrollbar.set)
    
    dict_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    dict_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # 绑定 Canvas 宽度变化事件，使内部 Frame 宽度跟随
    def on_canvas_configure(event):
        dict_scrollable_frame.configure(width=event.width)
    dict_canvas.bind("<Configure>", on_canvas_configure)
    
    def update_dict_display():
        # 清空之前的内容
        for widget in dict_scrollable_frame.winfo_children():
            widget.destroy()
        
        if not dictionary_files:
            label = ttk.Label(dict_scrollable_frame, text="(暂无字典)", foreground="gray")
            label.pack(anchor=tk.W, padx=5, pady=5)
        else:
            for i, fpath in enumerate(dictionary_files):
                count = len(dictionary_pools.get(fpath, []))
                
                # 为每个字典创建一行（使用 grid 更好地控制布局）
                item_frame = ttk.Frame(dict_scrollable_frame)
                item_frame.pack(anchor=tk.W, fill=tk.BOTH, expand=True, padx=3, pady=3)
                item_frame.columnconfigure(0, weight=1)  # 复选框占满可用宽度
                
                # 启用/禁用复选框
                is_enabled = dictionary_enabled.get(fpath, True)
                enable_var = tk.BooleanVar(value=is_enabled)
                
                def make_toggle(filepath, var):
                    def toggle_dict():
                        global dictionary_enabled
                        dictionary_enabled[filepath] = var.get()
                        save_config()
                        log_info(f"字典 {os.path.basename(filepath)} 已{'启用' if var.get() else '禁用'}")
                    return toggle_dict
                
                check = ttk.Checkbutton(item_frame, text=os.path.basename(fpath), variable=enable_var, 
                                       command=make_toggle(fpath, enable_var))
                check.grid(row=0, column=0, sticky=tk.W+tk.E, padx=5)
                
                # 显示记录数
                count_label = ttk.Label(item_frame, text=f"({count}条)", foreground="gray", font=("微软雅黑", 8))
                count_label.grid(row=0, column=1, sticky=tk.W, padx=5)
                
                # 删除按钮
                def make_delete(filepath):
                    def delete_dict():
                        global dictionary_files, dictionary_pools, dictionary_enabled
                        if messagebox.askyesno("确认", f"确定要删除字典:\n{os.path.basename(filepath)}"):
                            if filepath in dictionary_files:
                                dictionary_files.remove(filepath)
                                del dictionary_pools[filepath]
                                del dictionary_enabled[filepath]
                                update_dict_display()
                                total_words = sum(len(words) for words in dictionary_pools.values())
                                if dictionary_files:
                                    dict_list_label.config(
                                        text=f"字典列表: ({len(dictionary_files)} 个字典, 共 {total_words} 条记录)", 
                                        foreground="green"
                                    )
                                else:
                                    dict_list_label.config(text="字典列表: (未加载)", foreground="gray")
                                save_config()
                                log_info(f"字典已删除: {os.path.basename(filepath)}")
                    return delete_dict
                
                del_btn = ttk.Button(item_frame, text="×删除", width=6, command=make_delete(fpath))
                del_btn.grid(row=0, column=2, sticky=tk.E, padx=2)
    
    def select_dictionary():
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="选择字典文件 (UTF-8)",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filepath:
            if load_dictionary(filepath):
                update_dict_display()
                total_words = sum(len(words) for words in dictionary_pools.values())
                dict_list_label.config(
                    text=f"字典列表: ({len(dictionary_files)} 个字典, 共 {total_words} 条记录)", 
                    foreground="green"
                )
                save_config()
            else:
                messagebox.showerror("加载失败", f"字典加载失败或已存在:\n{filepath}")
    
    def clear_all_dictionaries():
        global dictionary_files, dictionary_pools, dictionary_enabled
        if dictionary_files:
            if messagebox.askyesno("确认", f"确定要删除全部 {len(dictionary_files)} 个字典吗?"):
                dictionary_files.clear()
                dictionary_pools.clear()
                dictionary_enabled.clear()
                update_dict_display()
                dict_list_label.config(text="字典列表: (未加载)", foreground="gray")
                save_config()
                log_info("所有字典已清除")
    
    button_dict_frame = ttk.Frame(main_frame)
    button_dict_frame.grid(row=9, column=0, columnspan=2, sticky=tk.EW, pady=5)
    ttk.Button(button_dict_frame, text="添加字典", command=select_dictionary, width=15).pack(side=tk.LEFT, padx=2)
    ttk.Button(button_dict_frame, text="清除全部字典", command=clear_all_dictionaries, width=15).pack(side=tk.LEFT, padx=2)
    
    def apply():
        global time_interval, input_length, send_with_ctrl
        try:
            time_interval = interval_var.get()
            input_length = length_var.get()
            send_with_ctrl = send_method_var.get()
            save_config()
            log_info("配置已成功应用并保存至本地")
            messagebox.showinfo("成功", "配置已应用")
        except: 
            messagebox.showerror("错误", "请输入有效的数值")

    ttk.Button(main_frame, text="保存并应用配置", command=apply).grid(row=10, column=0, columnspan=2, pady=10)

    # --- 状态与日志 ---
    ttk.Separator(main_frame, orient='horizontal').grid(row=11, column=0, columnspan=2, sticky="ew", pady=10)

    status_label = tk.Label(main_frame, text="状态: 已停止", font=("微软雅黑", 11, "bold"), fg="blue")
    status_label.grid(row=12, column=0, columnspan=2, pady=5)

    # --- 控制按钮 ---
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=13, column=0, columnspan=2, sticky=tk.EW, pady=10)
    ttk.Button(button_frame, text="启动监控", command=start_worker, width=15).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="停止监控", command=stop_worker, width=15).pack(side=tk.LEFT, padx=5)

    log_header_frame = ttk.Frame(main_frame)
    log_header_frame.grid(row=14, column=0, columnspan=2, sticky=tk.W, pady=(10, 2))
    ttk.Label(log_header_frame, text="实时运行日志:").pack(side=tk.LEFT)
    ttk.Button(log_header_frame, text="清空日志", command=clear_logs, width=10).pack(side=tk.LEFT, padx=10)

    log_display = scrolledtext.ScrolledText(main_frame, height=12, width=70, font=("Consolas", 9), bg="#f8f8f8")
    log_display.grid(row=15, column=0, columnspan=2, sticky=tk.NSEW)

    # --- 快捷键提示 ---
    footer_label = ttk.Label(main_frame, text="全局快捷键: Ctrl + Alt + Q (启动/停止)", foreground="gray")
    footer_label.grid(row=16, column=0, columnspan=2, pady=15)

    # 注册快捷键
    try:
        keyboard.add_hotkey("ctrl+alt+q", toggle_worker)
        log_info("热键 Ctrl+Alt+Q 注册成功")
    except Exception as e:
        log_info(f"热键注册失败: {e}")
    
    # 初始化字典显示
    update_dict_display()
    log_info("程序启动完成，等待操作。")
    
    # 窗口居中
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    run_gui()
