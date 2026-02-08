import os
import time
from colorama import Fore, Style, init

init()

def get_stats():
    base = "backend/data/queue"
    return {
        "OBSERVE": len(os.listdir(f"{base}/1_inbox")),
        "DECIDE": len(os.listdir(f"{base}/2_processing")),
        "ACT_OK": len(os.listdir(f"{base}/3_approved")),
        "ACT_FAIL": len(os.listdir(f"{base}/3_rejected")),
        "VAULT": len(os.listdir("backend/data/konza_vault"))
    }

def draw_dashboard():
    while True:
        s = get_stats()
        os.system('clear')
        print(f"{Fore.CYAN}🏛️  UHAKIKI-AI KONZA MONITORING DASHBOARD{Style.RESET_ALL}")
        print("-" * 40)
        print(f"{Fore.YELLOW}  [1] OBSERVE (Inbox):   {s['OBSERVE']} files{Style.RESET_ALL}")
        print(f"{Fore.BLUE}  [2] DECIDE (Active):    {s['DECIDE']} files{Style.RESET_ALL}")
        print("-" * 40)
        print(f"{Fore.GREEN}  [3] ACT (Approved):     {s['ACT_OK']}{Style.RESET_ALL}")
        print(f"{Fore.RED}  [3] ACT (Rejected):     {s['ACT_FAIL']}{Style.RESET_ALL}")
        print("-" * 40)
        print(f"  [🔒] VAULT LOGS:        {s['VAULT']} entries")
        print("\nPress Ctrl+C to exit monitoring.")
        time.sleep(2)

if __name__ == "__main__":
    draw_dashboard()