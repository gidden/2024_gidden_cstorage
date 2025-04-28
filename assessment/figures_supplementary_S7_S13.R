library(tidyverse)
library(ggplot2)
library(readr)
library(stringr)
library(purrr)
library(gridExtra)
library(patchwork)
library(zoo)

############################
#Code to replicate Fig S7
############################

world_file <- "C:/2024_gidden_cstorage-main/data/raw/AR6_Scenarios_Database_World_v1.1.csv"
meta_file <- "C:/2024_gidden_cstorage-main/data/raw/meta.csv"
output_file <- "C:/2024_gidden_cstorage-main/data/derived/ccs_overview.csv"  


variables <- c("Carbon Sequestration|CCS", "Carbon Sequestration|CCS|Fossil", 
               "Carbon Sequestration|CCS|Biomass", "Carbon Sequestration|CCS|Industrial Processes", 
               "Carbon Sequestration|Direct Air Capture")

meta <- read_csv(meta_file) %>%
  select(Model, Scenario, Category, Category_name, NetZeroYear = `Year of netzero CO2 emissions (Harm-Infilled) Table SPM2`) %>%
  filter(Category %in% c("C1", "C2", "C3", "C4"))

category<-meta %>%
  select(Model, Scenario, Category, Category_name)

nz<-meta %>%
  select(Model, Scenario, NetZeroYear)


df <- read_csv(world_file) %>%
  filter(Variable %in% variables) %>%
  pivot_longer(cols = where(is.numeric),  
               names_to = "Year", values_to = "value") %>%
  mutate(Year = as.integer(Year)) %>%
  pivot_wider(id_cols = c(Model, Scenario, Region, Year), 
              names_from = Variable, values_from = value) %>%
  filter(!is.na(`Carbon Sequestration|CCS|Industrial Processes`)) %>%
  filter(Year > 2019) %>%
  inner_join(category) %>%
  mutate(`Carbon Sequestration|Direct Air Capture` = replace_na(`Carbon Sequestration|Direct Air Capture`, 0)) %>%
  rowwise() %>%
  mutate(CCS_Sum = sum(c_across(c(
    `Carbon Sequestration|CCS|Fossil`, 
    `Carbon Sequestration|CCS|Biomass`, 
    `Carbon Sequestration|CCS|Industrial Processes`, 
    `Carbon Sequestration|Direct Air Capture`
  )), na.rm = TRUE)) %>%
  ungroup() %>%
  mutate(Difference = abs(CCS_Sum - `Carbon Sequestration|CCS`)) %>%
  filter(Difference <= 500) %>%
  select(-CCS_Sum, -Difference)  # Drop temporary columns



df_expanded <- df %>%
  filter(Year > 2019) %>%
  select(-Region)%>%
  group_by(Model, Scenario, Category)%>%
  complete(Year = 2020:2100)  # Fill in missing years

df_interpolated <- df_expanded %>%
  ungroup()%>%
  group_by(Model, Scenario) %>%
  mutate(across(
    c(`Carbon Sequestration|CCS|Fossil`, 
      `Carbon Sequestration|CCS|Biomass`, 
      `Carbon Sequestration|CCS|Industrial Processes`, 
      `Carbon Sequestration|Direct Air Capture`),
    ~ na.approx(.x, na.rm = FALSE),  
    .names = "interp_{col}"
  )) %>%
  ungroup()


df_total <- df_interpolated %>%
  group_by(Model, Scenario, Category) %>%
  summarise(
    `CCS Fossil` = sum(`interp_Carbon Sequestration|CCS|Fossil`, na.rm = TRUE),
    `CCS Biomass` = sum(`interp_Carbon Sequestration|CCS|Biomass`, na.rm = TRUE),
    `CCS Industrial` = sum(`interp_Carbon Sequestration|CCS|Industrial Processes`, na.rm = TRUE),
    `Direct Air Capture` = sum(`interp_Carbon Sequestration|Direct Air Capture`, na.rm = TRUE),
    .groups = "drop"
  )



df_share <- df_total %>%
  rowwise() %>%
  mutate(Total_CCS = sum(c_across(`CCS Fossil`:`Direct Air Capture`), na.rm = TRUE)) %>%
  mutate(
    `CCS Fossil Share` = `CCS Fossil` / Total_CCS * 100,
    `CCS Biomass Share` = `CCS Biomass` / Total_CCS * 100,
    `CCS Industrial Share` = `CCS Industrial` / Total_CCS * 100,
    `Direct Air Capture Share` = `Direct Air Capture` / Total_CCS * 100
  ) %>%
  select(Category, `CCS Fossil Share`, `CCS Biomass Share`, `CCS Industrial Share`, `Direct Air Capture Share`) %>%
  pivot_longer(cols = -Category, names_to = "Sequestration Type", values_to = "Share Percentage")


custom_colors <- c(
  "CCS Fossil Share" = "#1f77b4",          
  "CCS Industrial Share" = "#7fdbff",       
  "CCS Biomass Share" = "#2ca02c",          
  "Direct Air Capture Share" = "#98df8a"    
)

sequestration_order <- c(
  "CCS Fossil Share", 
  "CCS Industrial Share", 
  "CCS Biomass Share", 
  "Direct Air Capture Share"
)


df_share$`Sequestration Type` <- factor(
  df_share$`Sequestration Type`, 
  levels = sequestration_order
)

ggplot(df_share, aes(x = `Sequestration Type`, y = `Share Percentage`, fill = `Sequestration Type`)) +
  geom_boxplot() +
  scale_fill_manual(values = custom_colors) +
  facet_wrap(~Category) +
  labs(title = "Share of cumulative CCS 2020 to 2100",
       x = "",
       y = "Percentage (%)") +
  theme_minimal() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position = "bottom",
    legend.title = element_blank()
  )



# Save the figure
ggsave("C:/2024_gidden_cstorage-main/figures/s7.jpeg", 
       width = 10, height = 6, dpi = 300)





############################
#Code to replicate Fig S13
############################


world_file <- "C:/2024_gidden_cstorage-main/data/raw/AR6_Scenarios_Database_World_v1.1.csv"
meta_file <- "C:/2024_gidden_cstorage-main/data/raw/meta.csv"
output_file <- "C:/2024_gidden_cstorage-main/data/derived/variable_reporting_breakdown.csv"  
figures_path <- "C:/2024_gidden_cstorage-main/figures"


meta <- read_csv(meta_file) %>%
  select(Model, Scenario, Category, Category_name, NetZeroYear = `Year of netzero CO2 emissions (Harm-Infilled) Table SPM2`) %>%
  filter(Category %in% c("C1", "C2", "C3", "C4"))

category<-meta %>%
  select(Model, Scenario, Category, Category_name)

variables <- c("Carbon Sequestration|CCS", "Carbon Sequestration|CCS|Fossil", 
               "Carbon Sequestration|CCS|Biomass", "Carbon Sequestration|CCS|Industrial Processes", 
               "Carbon Sequestration|Direct Air Capture")



df <- read_csv(world_file) %>%
  filter(Variable %in% variables) %>%
  filter(Model!="REMIND-Buildings 2.0")%>%
  #POLES ENGAGE
  filter(Model!="POLES ENGAGE")%>%
  #POLES GECO2019
  filter(Model!="POLES GECO2019")%>%
  pivot_longer(cols = where(is.numeric),  
               names_to = "Year", values_to = "value") %>%
  mutate(Year = as.integer(Year)) %>%
  pivot_wider(id_cols = c(Model, Scenario, Region, Year), 
              names_from = Variable, values_from = value) %>%
  filter(!is.na(`Carbon Sequestration|CCS|Industrial Processes`)) %>%
  filter(Year > 2019) %>%
  inner_join(meta) %>%
  mutate(`Carbon Sequestration|Direct Air Capture` = replace_na(`Carbon Sequestration|Direct Air Capture`, 0)) %>%
  rowwise() %>%
  mutate(CCS_Sum = sum(c_across(c(
    `Carbon Sequestration|CCS|Fossil`, 
    `Carbon Sequestration|CCS|Biomass`, 
    `Carbon Sequestration|CCS|Industrial Processes`, 
    `Carbon Sequestration|Direct Air Capture`
  )), na.rm = TRUE)) %>%
  ungroup() %>%
  mutate(Difference = abs(CCS_Sum - `Carbon Sequestration|CCS`)) %>%
  filter(Difference <= 500) %>%
  select(-CCS_Sum, -Difference)%>%
  mutate(scenario_id = paste(Model, Scenario, sep = "_")) 




total_ccs <- ggplot(df, aes(x = Year, y = `Carbon Sequestration|CCS`/1000, group = scenario_id)) +
  geom_line(alpha = 0.7, color = "grey") +
  geom_segment(data = data.frame(
    x = c(2040, 2050, 2050, 2050),
    xend = c(2040, 2050, 2050, 2050),
    y = c(0, 0, 0, 0),
    yend = c(4.3, 7, 8.6, 16),
    label = c("Kazlou et al 2024", "Warszawski et al 2021", "Grant et al 2022", "Zhang et al 2024")
  ), aes(x = x, y = y, xend = xend, yend = yend, group = label), 
  inherit.aes = FALSE,  # This prevents inheriting the scenario_id grouping
  linetype = "dashed", color = "royalblue") +
  theme_minimal() +
  labs(title = "Carbon Sequestration|CCS",
       x = "",
       y = "GtCO2/year",
       color = "Category") +
  facet_wrap(~ Category) +
  theme(legend.position = "bottom")

# Calculate percentage statistics by category
constraints <- data.frame(
  x = c(2040, 2050, 2050, 2050),
  y = c(4.3, 7, 8.6, 16),
  label = c("Kazlou et al 2024", "Warszawski et al 2021", "Grant et al 2022", "Zhang et al 2024"),
  threshold = c(4.3, 7, 8.6, 16),
  year = c(2040, 2050, 2050, 2050)
)

# Get all unique categories
categories <- unique(df$Category)

label_data <- do.call(rbind, lapply(categories, function(cat) {
  do.call(rbind, lapply(1:nrow(constraints), function(i) {
    threshold <- constraints$threshold[i]
    year_to_check <- constraints$year[i]
    
    # Filter data for specific category and year
    cat_year_data <- df[df$Year == year_to_check & df$Category == cat, ]
    
    # Calculate percentage exceeding threshold for this category
    if(nrow(cat_year_data) > 0) {
      n_scenarios <- length(unique(cat_year_data$scenario_id))
      if(n_scenarios > 0) {
        n_exceeding <- sum(tapply(cat_year_data$`Carbon Sequestration|CCS`/1000, 
                                  cat_year_data$scenario_id, 
                                  function(x) any(x > threshold)))
        pct <- round(n_exceeding / n_scenarios * 100)
        
        # Create formatted label with percentage on left side
        label_text <- paste0(pct, "% > ", threshold, " (", constraints$label[i], ")")
      } else {
        label_text <- paste0("0% > ", threshold, " (", constraints$label[i], ")")
      }
    } else {
      label_text <- paste0("NA% > ", threshold, " (", constraints$label[i], ")")
    }
    

    data.frame(
      x = constraints$x[i],
      y = constraints$y[i],
      label = label_text,
      Category = cat
    )
  }))
}))

# Add the text labels to the plot
total_ccs <- total_ccs + 
  geom_text(data = label_data, 
            aes(x = x, y = y, label = label),
            hjust = -0.1, vjust = -0.5, size = 3,
            inherit.aes = FALSE)

total_ccs


# Save the combined figure
ggsave("C:/2024_gidden_cstorage-main/figures/s13.jpeg", 
       total_ccs, width = 8, height = 8, dpi = 300)