# BG Grapher
Simple python application that connects multiple blood glucose related apps to allow easy graphing and pattern analysis on PC.

### How it works

This app grabs data from Dexcom, Libre, and other apps, including food logging apps such as MyFitnessPal, using OAuth2 requests.

The data retrieved is then graphed and can be reviewed in order to find trends in high or low glucose, and patterns related to food intake.

Overall glucose data is also given as a percentage in target, which can be configured to your prefrence.

### TODO
Integrate MyFitnessPal, Libre Sensor

Actually make graphing application part

Rewrite callback server code to allow it to be used by multiple applications

Create UI (possibly using tkinter)

Create configureable % in range targets

