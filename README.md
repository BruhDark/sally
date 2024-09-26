# 🦮 Sally

Sally is an open-source Discord bot that handles different specific features. It mainly serves as a Roblox verification bot as of now. 

Sally is just a personal bot to work and improve my skills with the library and language. It was designed to only serve 1 Discord server, which means settings are based off that specific server requirements (role IDs for checks, channel IDs, blab blah).

# 🎾 Features
Sally's main features consist of:
- Roblox verification, with code and game verification methods. Storing user's verifications in MongoDB.
- "Internal" (because it is technically publicly accessible but endpoints require a simple authorization) API that allows the Roblox verification game to communicate with Sally. This API also allows WePeak (the specific Roblox group Sally serves) to lock their main game only allowing verified users and/or users who meet a certain criteria by hitting specific endpoints that give back information for the lock to allow the user or not unto the game.
- Miscellaneous user-installable commands such as RTFM, AI prompts provided by Groq's models and translate commands.
- Other small features that are probably irrelevant.
