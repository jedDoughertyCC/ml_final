########################
#money_cleanup.R
#Jed Dougherty and Devin Jones
#Reads in basic money data
#cleans it, and adds necessary variables
########################
library(RCurl)
library(rjson)
library(sqldf)
library(lubridate)
library(scales)
prod_numbers <- read.csv("prod_numbers.txt",sep = ";")

# Reads in movie information from imdb csv file
movies_imdb <- read.csv("movies_imdb.csv", stringsAsFactors = FALSE)

#Function to trim whitespace
trim <- function(x){
  gsub("^\\s+|\\s+$", "", x)
}

#Function to change factor to numeric
as.numeric.factor <- function(x) {(as.numeric(as.character(x)))[x]}

#converts dollars to numbers
dollar_converter <- function(x){
  converted <- as.numeric(gsub(",","",gsub("\\$","",x)))
  return(converted)
}

#given a column name, creates columns for all subsets of column
get_uniques <- function(x){
  names_all<- x
  names_all <- paste(names_all,collapse = ", ")
  names_df <- data.frame(strsplit(names_all,", "))
  names(names_df) <- "names"
  unique_names <- unique(names_df$names)
  return(unique_names)
}

#gets boolean for each new column
add_columns <- function(y,uniques,df){
  cframe <- df
  for(i in 1:length(uniques)) {
    cols <- length(colnames(cframe))
    cframe <- cbind(cframe,
                              as.numeric(grepl(uniques[i],cframe[, y])))
    colnames(cframe)[cols+1] <- gsub(" ","_",uniques[i])
  }
  return(cframe)
}

#Uses sql to rough match Actors to their movies
get_prior_earnings <- function(unique_list,df,columnname){
  small_df <- df[,c("Title",columnname,"worldwide_raw",
                                   "earnings_ratio","Release.Date")]
  unique_df <- data.frame(unique_list)
  colnames(unique_df) <- "unique_l"
  combo_df <- sqldf(paste("
                          SELECT * from
                          unique_df
                          join small_df on ",
                          columnname,
                          " like
                          ('%' || unique_l ||'%');
                          ", sep = ""), drv = "SQLite")

  prior_earnings <- sqldf(paste("
                          SELECT
                          current.Title,
                          avg(coalesce(prior.worldwide_raw,0)) avg_prior_",columnname,"_total,
                          avg(coalesce(prior.earnings_ratio,1)) avg_prior_",columnname,"_ratio
                          FROM
                          combo_df current
                          left outer join
                          combo_df prior on
                          (current.unique_l = prior.unique_l
                           and current.Release_date > prior.Release_date)
                          GROUP BY
                          current.Title;
                          ", sep = ""),drv = "SQLite")
  return(prior_earnings)
}

#converts the text of the budget to raw numbers
prod_numbers$budget_raw <- dollar_converter(prod_numbers$Production.Budget)

#converts the text of the worldwide earnings to raw numbers
prod_numbers$worldwide_raw <- dollar_converter(prod_numbers$Worldwide.Gross)

#converts the text of the worldwide earnings to raw numbers
prod_numbers$domestic_raw <- dollar_converter(prod_numbers$Domestic.Gross)

#calculates whether each movie broke even
prod_numbers$break_even <- as.numeric(prod_numbers$worldwide_raw > prod_numbers$budget_raw)
prod_numbers[prod_numbers$break_even == 0,]$break_even = -1

#calculates whether each movie was a big earner
prod_numbers$big_money <- as.numeric(prod_numbers$worldwide_raw > prod_numbers$budget_raw*2)
prod_numbers[prod_numbers$big_money == 0,]$big_money = -1


#calculates the earnings ratio of each movie
prod_numbers$earnings_ratio <- prod_numbers$worldwide_raw/prod_numbers$budget_raw

#calculates the gain or loss percentage of each movie
prod_numbers$gain_loss <- (prod_numbers$worldwide_raw - prod_numbers$budget_raw)/prod_numbers$budget_raw

#reformat date
prod_numbers$Release.Date <- as.Date(prod_numbers$Release.Date,format='%m/%d/%Y')

#calculates the number of other movies being released in the same time frame
#We don't use this since you wouldnt know until
#after the decision to produce was made
releases_by_week <- aggregate(Movie ~ floor_date(Release.Date,"week"),
                              data = prod_numbers,
                              FUN = length)

#reformats dates to date field
#and removes films that did not make money
prod_numbers_lim <- prod_numbers[prod_numbers$Release.Date < as.Date("2014-01-01") &
                                 prod_numbers$Release.Date >= as.Date("2000-01-01"),]
prod_numbers_lim <- prod_numbers_lim[prod_numbers_lim$domestic_raw > 1 &
                                 prod_numbers_lim$worldwide_raw > 1, ]


#identify nas in movies database
#In Genre we want to replace na with a text field
movies_imdb$Genre <- gsub("N/A","Not Available",movies_imdb$Genre)

#Everywhere else we want to remove rows that include an NA value
missing_values <- movies_imdb == "N/A"
movies_imdb[missing_values] <- NA

#Remove unnecessary columns and perform other cleanup on movies_imdb
movies_imdb$Metascore  <- NULL
movies_imdb$Poster     <- NULL
movies_imdb$Plot       <- NULL
movies_imdb$Language   <- NULL
movies_imdb$Country    <- NULL
movies_imdb$Runtime    <- as.numeric(gsub(" min","",movies_imdb$Runtime))
movies_imdb$Writer     <- gsub(" \\(.*\\)","",movies_imdb$Writer)
movies_imdb            <- movies_imdb[movies_imdb$Type == "movie",]
movies_imdb$Type       <- NULL
movies_imdb$Response   <- NULL
movies_imdb            <- na.omit(movies_imdb)
movies_imdb$Year       <- as.numeric(movies_imdb$Year)
movies_imdb            <- movies_imdb[movies_imdb$Year > 2000,]
movies_imdb$imdbVotes  <- NULL
movies_imdb$imdbRating <- as.numeric(movies_imdb$imdbRating)
# Merges movie information with production information
movies_imdb_prod <- merge(movies_imdb,prod_numbers_lim,
                          by.x = "Title",
                          by.y = "Movie")

# Filters out accidental non-movie matches

# Clean up specific stuff at the end of the writer column

# Gets list of actors and checks if they are in each movie
unique_actors    <- get_uniques(movies_imdb_prod$Actors)
unique_writers   <- get_uniques(movies_imdb_prod$Writer)
unique_directors <- get_uniques(movies_imdb_prod$Director)
unique_genres    <- get_uniques(movies_imdb_prod$Genre)

# Gets the average prior earnings of actors, writers, and directors
# for each movie
p_actors    <- get_prior_earnings(unique_actors, movies_imdb_prod, "Actors")
p_writers   <- get_prior_earnings(unique_writers, movies_imdb_prod, "Writer")
p_directors <- get_prior_earnings(unique_directors, movies_imdb_prod, "Director")

#merges the informaton in
movies_imdb_prod <- merge(movies_imdb_prod,p_actors, by = "Title")
movies_imdb_prod <- merge(movies_imdb_prod,p_writers, by = "Title")
movies_imdb_prod <- merge(movies_imdb_prod,p_directors, by = "Title")
# TOGGLE: turns on and off whether we look at each actor individually
# movies_imdb_prod <- add_columns("Actors",unique_actors,movies_imdb_prod)

movies_imdb_prod <- add_columns("Genre",unique_genres,movies_imdb_prod)
movies_imdb_prod$Title <- NULL
movies_imdb_prod$Rated <- NULL
movies_imdb_prod$Released <- NULL
movies_imdb_prod$Runtime <- NULL
movies_imdb_prod$Genre <- NULL
movies_imdb_prod$Director <- NULL
movies_imdb_prod$Actors <- NULL
movies_imdb_prod$Writer <- NULL
movies_imdb_prod$Awards <- NULL
movies_imdb_prod$Release.Date <- NULL
movies_imdb_prod$Production.Budget <- NULL
movies_imdb_prod$Domestic.Gross <- NULL
movies_imdb_prod$Worldwide.Gross <- NULL
movies_imdb_prod$gain_loss <- NULL

#zeroing out output variables
# movies_imdb_prod$worldwide_raw <- NULL
# movies_imdb_prod$domestic_raw <- NULL
# movies_imdb_prod$big_money <- NULL
movies_imdb_prod$break_even <- NULL
movies_imdb_prod$imdbID <- NULL
# movies_imdb_prod$imdbRating <- NULL
movies_imdb_prod$earnings_ratio <- NULL

movies_imdb_prod <- unique(movies_imdb_prod)




# Writes output file to csv
write.csv(movies_imdb_prod,"data_with_booleans.csv", row.names = FALSE)

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
