API wrapper for [princess connect re:dive(tw server)](http://www.princessconnect.so-net.tw/)

originated from [cc004/pcrjjc2](https://github.com/cc004/pcrjjc2)

# usage

please read src in `example/`, major usages included

> REMINDER: THE EXAMPLES WERE WRITTEN WHEN PCR VERSION 2.8.1
>
> PLEASE CHECK `vesion` ARGUMENT IS UPDATED IN FUNCTION `PCRClient()` CALL WHEN USE

`load_index.py`: dump account data

`pkg_decoder.py`: decode raw encoded package, capture packages yourself
> meme: I use Android simulator + Android proxy + Fiddler to catch packages

`tutorial.py`: give it a newly created account playerprefs, it will pass the tutorial and some main quests
