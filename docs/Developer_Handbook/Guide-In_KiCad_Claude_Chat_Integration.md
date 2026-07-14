# Guide: Direct Claude 3.5 Sonnet API Chat Integration inside KiCad

[Home](../../README.md) › [Project Index](../../PROJECT_INDEX.md) › [Developer Handbook](README.md) › In-KiCad Claude Chat Integration

> **Status:** Draft
> **Owner:** Project maintainers
> **Applies To:** KiCad AI Integration developers
> **Authoritative:** No

### Guide: Direct Claude 3.5 Sonnet API Chat Integration inside KiCad

You do not have to constantly export data and copy-paste it into an external browser tab. Because KiCad exposes its internal python data layer (`pcbnew`) and utilizes an open-source graphical layout library (`wxPython`), you can run interactive, multi-turn AI chat interfaces directly inside your electronic design workspace using your own Anthropic API key.

For a specialized Bedini/Babcock circuit, this allows you to ask the AI dynamic questions about high-voltage loops or Pi Pico firmware adjustments right next to your open design canvas.

---

### 1. Native KiCad AI Plugins

The open-source community maintains dedicated, drop-in plugins that open interactive chat windows inside your schematic or layout editor.

### K-AI Plugin for KiCad

- **What it is**: An open-source, community-driven conversational assistant designed to sit inside your toolbars.
- **How it works**: You clone the repository into your local KiCad `plugins` directory and input your Anthropic API key into the settings menu.
- **Capabilities**: It draws an interactive chat window pane directly over or alongside your design. You can text-chat with Claude 3.5 Sonnet to discuss parts selection, calculate trace sizes, or query specific nets without minimizing KiCad.

---

### 2. The Model Context Protocol (MCP) Approach

If you prefer using Anthropic's official tools (such as the desktop Claude application or terminal-based Claude Code), you can turn KiCad into an AI-accessible platform using the open-source **Model Context Protocol (MCP)**.

### KiCad MCP Server

- **The Architecture**: MCP is an open standard that allows an external AI chat application to safely read data from local computer files or local software APIs.
- **The Workflow**:
    1. You run a lightweight, open-source local server script on your machine that communicates with KiCad’s internal Python API.
    2. You point your Claude Desktop App or developer command-line chat to that local server.
    3. You use your Anthropic API key to open an interactive chat session anywhere on your desktop.
- **Usage Example**: Instead of running scripts manually, you can simply type into your interactive chat window: _"Claude, look at my currently open KiCad board layout. Is the trace for the high-voltage flyback recapture loop wide enough to safely handle 5A surges?"_ The AI will call the local KiCad API automatically, read the project data, and print the answer inside your chat window.

---

### 3. Light Python GUI Script (Zero-Installation Console Method)

If you do not want to install external plugins or modify your system configuration, you can use KiCad's built-in **Scripting Console** to generate an interactive chat window on the fly.

Running the script below inside KiCad's **Tools > Scripting Console** pops up a basic graphical UI window containing an API key field, an input box, and a running chat history.

python

```
import pcbnew
import wx
import urllib.request
import json

class KiCadAIChatWindow(wx.Frame):
    def __init__(self, parent, title):
        super(KiCadAIChatWindow, self).__init__(parent, title=title, size=(450, 500))
        
        # Setup UI Panel and layout positioning
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # API Key Input Row
        hbox_key = wx.BoxSizer(wx.HORIZONTAL)
        lbl_key = wx.StaticText(panel, label="Anthropic API Key: ")
        self.txt_key = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        hbox_key.Add(lbl_key, flag=wx.RIGHT, border=8)
        hbox_key.Add(self.txt_key, proportion=1)
        vbox.Add(hbox_key, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        
        # Chat History Log Window
        self.chat_log = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_READONLY)
        vbox.Add(self.chat_log, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        
        # User Prompt Input Box
        self.user_input = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.user_input.Bind(wx.EVT_TEXT_ENTER, self.on_send)
        vbox.Add(self.user_input, flag=wx.EXPAND|wx.ALL, border=10)
        
        # Send Button
        btn_send = wx.Button(panel, label="Send to Claude")
        btn_send.Bind(wx.EVT_BUTTON, self.on_send)
        vbox.Add(btn_send, flag=wx.ALIGN_RIGHT|wx.RIGHT|wx.BOTTOM, border=10)
        
        panel.SetSizer(vbox)
        self.Show()

    def on_send(self, event):
        user_text = self.user_input.GetValue().strip()
        api_key = self.txt_key.GetValue().strip()
        
        if not user_text or not api_key:
            wx.MessageBox("Please fill in both your API Key and your chat question.", "Missing Information", wx.OK | wx.ICON_WARNING)
            return
            
        self.chat_log.AppendText(f"You: {user_text}\n\n")
        self.user_input.Clear()
        
        # Automatically grab the current KiCad board data context to append to the query
        board = pcbnew.GetBoard()
        file_path = board.GetFileName()
        
        # Package the request payload explicitly for the Claude API
        url = "https://anthropic.com"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1000,
            "messages": [{
                "role": "user",
                "content": f"Context: Operating in KiCad on project file {file_path}. Question: {user_text}"
            }]
        }
        
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                claude_reply = res_data['content'][0]['text']
                self.chat_log.AppendText(f"Claude: {claude_reply}\n\n-----------------\n\n")
        except Exception as e:
            self.chat_log.AppendText(f"System Error Connecting to Claude API: {str(e)}\n\n")

# Main execution inside KiCad scripting console environment
app = wx.GetApp() or wx.App(False)
frame = KiCadAIChatWindow(None, title="Live Claude 3.5 Sonnet Terminal")
```

Use code with caution.

---

### 4. Operational Best Practices

- **API Cost Control**: Because high-resolution images or complete text netlists consume significant input tokens, avoid sending the full schematic file with every single conversational message. Use an image attachment during your initial layout system audit prompt, and use text-only conversations for mid-design tweaking.
- **Security & Key Safety**: Avoid hardcoding your Claude API key directly into shared python files or script fields. Use environmental variables or entry windows that mask the key as a password field (like the script example above) so it stays securely on your machine.