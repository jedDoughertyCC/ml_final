########################
#money_cleanup.R
#Jed Dougherty and Devin Jones
#Reads in basic money data
#cleans it, and adds necessary variables
########################

prod_numbers <- read.csv("prod_numbers.txt",sep = ";")

#converts the text of the budget to raw numbers
prod_numbers$budget_raw <- as.numeric(gsub(",","",gsub("\\$","",prod_numbers$Production.Budget)))


#converts the text of the worldwide earnings to raw numbers
prod_numbers$gross_raw <- as.numeric(gsub(",","",gsub("\\$","",prod_numbers$Worldwide.Gross)))

#calculates whether each movie broke even
prod_numbers$break_even <- prod_numbers$gross_raw > prod_numbers$budget_raw


#calculates whether each movie was a big earner
prod_numbers$big_money <- prod_numbers$gross_raw > prod_numbers$budget_raw*3

#calculates the earnings ratio of each movie
prod_numbers$earnings_ratio <- prod_numbers$gross_raw/prod_numbers$budget_raw


