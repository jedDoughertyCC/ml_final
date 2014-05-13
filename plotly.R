# install.packages("devtools")
library("devtools")
# install_github("plotly", "ropensci")

library("plotly")
options(scipen=999)
py <- plotly(username="jediv", key="vt611etpzm")

source("money_cleanup.R")

plotter <- data.frame(prod_numbers_lim$Movie,
                      prod_numbers_lim$break_even,
                      round(prod_numbers_lim$earnings_ratio,2),
                      round(prod_numbers_lim$budget_raw,2),
                      prod_numbers_lim$Worldwide.Gross,
                      prod_numbers_lim$Production.Budget)

names(plotter) <- c("movie","break_even","earnings_ratio","budget_raw",
                    "worldwide_gross","production_budget")

plotter$even <- "Made money"

plotter[plotter$break_even == 0,]$even <- "Lost money"




movie_plot <- ggplot(plotter,aes(budget_raw,earnings_ratio)) +
              geom_point(aes(colour = factor(break_even)), alpha = .7) +
              scale_y_log10()

write.csv(plotter,"simple_movie_info.csv",quote = TRUE,row.names = FALSE)
# r <- py$ggplotly(movie_plot)


