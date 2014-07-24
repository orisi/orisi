from irc.bot import SingleServerIRCBot

CHANNEL = "#orisi-chan"
NICKNAME = "orisi-testbot"
SERVER = "irc.freenode.com"

class IrcBot(SingleServerIRCBot):
  def __init__(self, channel, nickname, server, port=6667):
    super(IrcBot, self).__init__([(server, port)], nickname, nickname)
    self.channel = channel

  def on_welcome(self, c, e):
    c.join(self.channel)

  def on_nicknameinuse(self, c, e):
    c.nick(c.get_nickname() + "_")

  def on_pubmsg(self, c, e):
    print e.type
    print e.source
    print e.target
    print e.arguments


def main():
  tb = IrcBot(CHANNEL, NICKNAME, SERVER)
  tb.start()

if __name__=="__main__":
  main()
