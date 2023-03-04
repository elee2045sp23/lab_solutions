#define EAP_ANONYMOUS_IDENTITY "" 
#define EAP_IDENTITY "kjohnsen@uga.edu" 
#define EAP_PASSWORD "" //password for eduroam account
#define WPA_PASSWORD "" //password for home wifi
#define USE_EAP
//SSID NAME
#ifdef USE_EAP
  const char* ssid = "eduroam"; // eduroam SSID
#else 
  const char* ssid = "shamrock"; // home SSID
#endif
