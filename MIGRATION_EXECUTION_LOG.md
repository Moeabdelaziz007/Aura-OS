[0;35m🚀 AetherOS: Initiating Firebase Migration...[0m
[0;34m🔍 Phase 1: Verifying Firebase CLI...[0m
✅ Firebase CLI version: [0;32m14.18.0[0m
[0;34m🏗️ Phase 2: Firebase Project Configuration...[0m
📍 Firebase Project ID: [0;32mnotional-armor-456623-e8[0m
[0;34m🔐 Phase 3: Firebase Authentication...[0m
✅ Already logged in.
[0;34m🏗️ Phase 4: Project Initialization...[0m
- Preparing the list of your Firebase projects
✔ Preparing the list of your Firebase projects
Now using project notional-armor-456623-e8
✅ Firebase project configured: [0;32mnotional-armor-456623-e8[0m
[0;34m📡 Phase 5: Activating Firebase Services...[0m
ERROR: (gcloud.firestore.databases.create) [amrikyy@gmail.com] does not have permission to access projects instance [notional-armor-456623-e8] (or it may not exist): This API method requires billing to be enabled. Please enable billing on project notional-armor-456623-e8 by visiting https://console.developers.google.com/billing/enable?project=notional-armor-456623-e8 then retry. If you enabled billing for this project recently, wait a few minutes for the action to propagate to our systems and retry. This command is authenticated as amrikyy@gmail.com which is the active account specified by the [core/account] property.

=== Deploying to 'notional-armor-456623-e8'...

i  deploying firestore
i  firestore: ensuring required API firestore.googleapis.com is enabled...
✔  firestore: required API firestore.googleapis.com is enabled
i  firestore: ensuring required API firestore.googleapis.com is enabled...
i  firestore: reading indexes from firestore.indexes.json...
i  cloud.firestore: checking firestore.rules for compilation errors...

Error: Compilation errors in firestore.rules:
[E] 30:31 - timestamp is a package and cannot be used as variable name.
[E] 31:14 - timestamp is a package and cannot be used as variable name.
