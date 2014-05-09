########################
#money_cleanup.R
#Jed Dougherty and Devin Jones
#Reads in basic money data
#cleans it, and adds necessary variables
########################
library(RCurl)
library(rjson)

prod_numbers <- read.csv("prod_numbers.txt",sep = ";")

dollar_converter <- function(x){
  converted <- as.numeric(gsub(",","",gsub("\\$","",x)))
  return(converted)
}

#converts the text of the budget to raw numbers
prod_numbers$budget_raw <- dollar_converter(prod_numbers$Production.Budget)

#converts the text of the worldwide earnings to raw numbers
prod_numbers$worldwide_raw <- dollar_converter(prod_numbers$Worldwide.Gross)

#converts the text of the worldwide earnings to raw numbers
prod_numbers$domestic_raw <- dollar_converter(prod_numbers$Domestic.Gross)

#calculates whether each movie broke even
prod_numbers$break_even <- prod_numbers$worldwide_raw > prod_numbers$budget_raw

#calculates whether each movie was a big earner
prod_numbers$big_money <- prod_numbers$worldwide_raw > prod_numbers$budget_raw*3

#calculates the earnings ratio of each movie
prod_numbers$earnings_ratio <- prod_numbers$worldwide_raw/prod_numbers$budget_raw

#reformat date
prod_numbers$Release.Date <- as.Date(prod_numbers$Release.Date,format='%m/%d/%Y')


prod_numbers_lim <- prod_numbers[prod_numbers$Release.Date < as.Date("2014-01-01"),]
prod_numbers_lim <- prod_numbers[prod_numbers$domestic_raw > 1 &
                                 prod_numbers$worldwide_raw > 1, ]

# Reads in movie information from imdb csv file
movies_imdb <- read.csv("movies_imdb.csv",stringsAsFactors = FALSE)

# Merges with production Information
movies_imdb_prod <- merge(movies_imdb,prod_numbers_lim, by.x = "Title", by.y = "Movie")

# Filters out accidental other matches
movies_imdb_prod <- movies_imdb_prod[movies_imdb_prod$Type == "movie",]

#Uncomment to reread from IMDB api
# names <- gsub(" ","+",prod_numbers_lim$Movie)
# titles <- data.frame()
# # uri <- "http://api.rottentomatoes.com/api/public/v1.0/movies.json?apikey=68vg99gygrykq3ruuyzwg7tw&q="
# uri <- "http://www.imdbapi.com/?t="
# # for ( i in 1:length(names)) {
# for ( i in 1:length(names)) {
  # req <- paste(uri, names[i],
  # sep="")
  # u <- getURL(req)
  # j <- fromJSON(u)
  # if(length(names(j)) > 2){
  # titles <- rbind(titles, data.frame(j))
  # }
# }

# write.csv(titles,"movies_imdb.csv",row.names = FALSE)
