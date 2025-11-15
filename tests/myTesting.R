# Sys.setenv(ANBIMA_CLIENT_ID = "CLIENT_ID_HERE")
# Sys.setenv(ANBIMA_CLIENT_SECRET = "CLIENT_SECRET_HERE")

library(httr)
library(jsonlite)

# Set your credentials
client_id <- Sys.getenv("ANBIMA_CLIENT_ID", unset = "your_client_id")
client_secret <- Sys.getenv("ANBIMA_CLIENT_SECRET", unset = "your_client_secret")
auth <- base64_enc(paste0(client_id, ":", client_secret))

# 1. Get access token
auth_url <- "https://api.anbima.com.br/oauth/access-token"
auth_body <- list(grant_type = "client_credentials")
auth_headers <- add_headers(
  "Content-Type" = "application/json",
  "Authorization" = paste("Basic", auth)
)
auth_resp <- POST(auth_url, body = toJSON(auth_body, auto_unbox = TRUE), encode = "raw", auth_headers)
token <- content(auth_resp)$access_token

# 2. Use token to call ETTJ API
api_url <- "https://api-sandbox.anbima.com.br/feed/precos-indices/v1/titulos-publicos/curvas-juros"
api_headers <- add_headers(
  "client_id" = client_id,
  "access_token" = token,
  "Authorization" = paste("Bearer",token)
)
api_resp <- GET(api_url, api_headers)
result <- content(api_resp, as="parsed", encoding = "UTF-8")

