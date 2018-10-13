# DynamicSocialNetworkSimulation
DynamicSocialNetwork_VisualizationApplication.py:
we visualize a dynamic social network-Twitter which comprise 10 well-known users in social fields including politic, music, movie, education and healthy. Two main relations are considered in which the first is relation "follow" and relation "major topic" R_{MTP} for the later. Relation R_{MTP} will appear when two agents are interested in the common topic with a probability greater than threshold p_0. We considered that each user contain a probability distribution of five topics and R_{MTP} with p_0=0.3. Initially, a network is generated as soon as text information is crawled, pre-processed and text mining by ATM. Visualization demonstrates the structure of the network with 2 relations. After every 12 hours, newly tweets of users will automatically be scrapped and exist ATM model will be updated. Therefore, network will also be updated including relation "follow", relation "major topic" R_{MTP} and topic's distribution of users.
- Dataset folder: Contain textual information and author's information which is crawled from Twitter.
- Files User_Topics_Distribution_period0/User_Topics_Distribution_period1/User_Topics_Distribution_period2/User_Topics_Distribution_period3: Results from estimating topic's distribution of users using ATM over time period.
