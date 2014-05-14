library(e1071)
library(plyr)


source("money_cleanup.R")
#reads in the csv of movie data
movie_data <- read.csv("data_with_booleans.csv")


#rounds everything to two decimal points
movie_data <- ddply(movie_data, 2, function (x){round(x,2)})

#factorizes the categorical result
#we are trying to predict
movie_data$big_money <- as.factor(movie_data$big_money)

#creates a training set and test set randomly
#from the data. Train is 2/3 of data
index <- 1:nrow(movie_data)
testindex <- sample(index, trunc(length(index)/3))
testset <- movie_data[testindex,]
trainset <- movie_data[-testindex,]

#creates support vector machine from the data
svm.movies <- svm(big_money ~ .,
                  data = trainset,
                  cost = 10,
                  gamma = .8)


#Predicts test set based on svm
svm.pred <- predict(svm.movies,
                    testset[-4])

#Table output of predicted v test
confusion_mat <- table(pred = svm.pred, true = testset[,4])



print(summary(svm.pred))
print(summary(confusion_mat))
