########################
#money_cleanup.R
#Jed Dougherty and Devin Jones
#Reads in basic money data
#cleans it, and adds necessary variables
########################
library(RCurl)
library(rjson)
library(sqldf)
prod_numbers <- read.csv("prod_numbers.txt",sep = ";")


# Reads in movie information from imdb csv file
movies_imdb <- read.csv("movies_imdb.csv",stringsAsFactors = FALSE)


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
                          avg(prior.worldwide_raw) avg_prior_",columnname,"_total,
                          avg(prior.earnings_ratio) avg_prior_",columnname,"_ratio
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
prod_numbers$break_even <- prod_numbers$worldwide_raw > prod_numbers$budget_raw

#calculates whether each movie was a big earner
prod_numbers$big_money <- prod_numbers$worldwide_raw > prod_numbers$budget_raw*3

#calculates the earnings ratio of each movie
prod_numbers$earnings_ratio <- prod_numbers$worldwide_raw/prod_numbers$budget_raw

#calculates the gain or loss percentage of each movie
prod_numbers$gain_loss <- (prod_numbers$worldwide_raw - prod_numbers$budget_raw)/prod_numbers$budget_raw

#reformat date
prod_numbers$Release.Date <- as.Date(prod_numbers$Release.Date,format='%m/%d/%Y')

#calculates the number of other movies being released in the same time frame
releases_by_week <- aggregate(Movie ~ floor_date(Release.Date,"week"),
                              data = prod_numbers,
                              FUN = length)

#first calculates how many times each date appears
dates <- prod_numbers$Release.Date

#reformats dates to date field
#and removes films that did not make money
prod_numbers_lim <- prod_numbers[prod_numbers$Release.Date < as.Date("2014-01-01") &
                                 prod_numbers$Release.Date >= as.Date("2000-01-01"),]
prod_numbers_lim <- prod_numbers[prod_numbers$domestic_raw > 1 &
                                 prod_numbers$worldwide_raw > 1, ]

# Merges movie information with production Information
movies_imdb_prod <- merge(movies_imdb,prod_numbers_lim, by.x = "Title", by.y = "Movie")

# Filters out accidental non-movie matches
movies_imdb_prod <- movies_imdb_prod[movies_imdb_prod$Type == "movie",]

movies_imdb_prod$Genre <- gsub("N/A","Not Available",movies_imdb_prod$Genre)

#Clean up specific stuff at the end of the writer column
movies_imdb_prod$Writer <- gsub(" (.*)","",movies_imdb_prod$Writer)

# Gets list of actors and checks if they are in each movie
unique_actors <- get_uniques(movies_imdb_prod$Actors)

# TOGGLE: turns on and off whether
# movies_imdb_prod <- add_columns("Actors",unique_actors,movies_imdb_prod)

# Gets list of genres and checks if they apply to each movie
unique_genres    <- get_uniques(movies_imdb_prod$Genre)
movies_imdb_prod <- add_columns("Genre",unique_genres,movies_imdb_prod)

# Gets list of unique writers and directors
unique_writers   <- get_uniques(movies_imdb_prod$Writer)
unique_directors <- get_uniques(movies_imdb_prod$Director)

# Gets prior earnings for actors, writers, and directors
p_actors    <- get_prior_earnings(unique_actors, movies_imdb_prod, "Actors")
p_writers   <- get_prior_earnings(unique_writers, movies_imdb_prod, "Writer")
p_directors <- get_prior_earnings(unique_directors, movies_imdb_prod, "Director")

movies_imdb_prod <- merge(movies_imdb_prod,p_actors, by = "Title")
movies_imdb_prod <- merge(movies_imdb_prod,p_writers, by = "Title")
movies_imdb_prod <- merge(movies_imdb_prod,p_directors, by = "Title")
# Writes output file to csv
# write.csv(movies_imdb_prod,"data_with_booleans.csv", row.names = FALSE)

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
