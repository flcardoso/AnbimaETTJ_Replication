library("tidyverse")

In <- read.csv("output/ettj_parameters.csv")
View(In[In$grupo_indexador=="PREFIXADOS",])

In <- read.csv("output/ettj_nominal.csv")
View(In[In$du==2520,])

In <- read.csv("output/ettj_real.csv")
View(In)

df <- In %>%
    select(du, date, rate) %>%
    tidyr::pivot_wider(names_from = date, values_from = rate)
View(df)