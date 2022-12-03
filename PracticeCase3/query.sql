SELECT
  sum(totals_transactions) as total_trx_per_ch_group,
  channelGrouping,
  ARRAY_AGG(
    STRUCT(totals_transactions, parse_date('%Y%m%d', date) as parsed_date, geoNetwork_country)
    ORDER BY parse_date('%Y%m%d', date) ASC
  ) AS ch_grouped
FROM `data-to-insights.ecommerce.rev_transactions`
GROUP BY channelGrouping
