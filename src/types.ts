export type Nullable = number | null;
export interface Facility {
 facility_id:string; name:string; district:string; region:string; address:string; method:string; process_key:string;
 year:number; capacity_m3_day:number; inflow_m3_day:Nullable; outflow_m3_day:Nullable; electricity_kwh:Nullable;
 annual_inflow_m3:Nullable; kwh_m3:Nullable; kwh_kg_bod:Nullable; bod_in:Nullable; bod_out:Nullable;
 toc_in:Nullable; toc_out:Nullable; tn_in:Nullable; tn_out:Nullable; tp_in:Nullable; tp_out:Nullable;
 bod_removal_pct:Nullable; toc_removal_pct:Nullable; tn_removal_pct:Nullable; tp_removal_pct:Nullable;
 indirect_tco2e_est:Nullable; reported_co2_kg_m3:Nullable; self_sufficiency_pct:Nullable; energy_production_toe:Nullable;
 utilization_pct:Nullable; benchmark_eligible:boolean; scale:string; flags:string[];
 rank_volume:Nullable; rank_bod:Nullable; rank_change:Nullable; national_percentile:Nullable;
}
export interface Summary { n:number; energy_valid_n:number; intensity_valid_n:number; electricity_kwh:number; annual_inflow_m3:number; weighted_kwh_m3:number; mean_kwh_m3:number; median_kwh_m3:number; median_bod_removal_pct:number; indirect_tco2e_est:number; benchmark_n:number; }
export interface Peer {available:boolean; reason?:string; count:number; ratio?:number; median_kwh_m3?:number; q25_kwh_m3?:number; q75_kwh_m3?:number; percentile?:number; peer_bod_removal_median?:number; peers?:{facility_id:string;name:string;region:string;kwh_m3:number;distance:number}[];}
export interface MapCoordinate {facility_id:string;latitude:number;longitude:number;status:'verified'|'estimated';basis:string;area_name:string|null;source_address:string|null;source_url:string;reference_year:number|null;attribution:string|null;note:string|null;}
export interface Insight { title:string; value:string; unit:string; finding:string; comparison:string; policy:string; limitation:string; source:string; year:number; }
export interface Score {mae:number;rmse:number;r2:number;n:number;}
export interface Prediction {facility_id:string;name:string;actual:number;predicted:number;residual:number;ratio:number;rf_predicted:number;baseline_predicted:number;xgb_predicted:number;}
export interface ShapContribution {key:string;feature:string;value:number|string|null;shap_value:number;rank:number;}
export interface ShapPrediction {facility_id:string;name:string;base_value:number;predicted_log:number;predicted:number;reconstructed_predicted:number;additivity_error:number;contributions:ShapContribution[];}
export interface ShapAnalysis {
 available:boolean;reason?:string;model:string;scale:string;method:string;scope:string;n:number;background_n:number;base_value:number;
 features:{key:string;label:string}[];importance:{key:string;feature:string;mean_abs:number;rank:number}[];predictions:ShapPrediction[];max_additivity_error:number;note:string;
}
export interface OperationalAPI {
 available:boolean;reason?:string;year:number;source_url:string;request_days:number;complete_request_days:number;raw_records:number;operation_days:number;start_date:string;end_date:string;source_sites:string[];effluent_sites:string[];effluent_records:number;valid_effluent_records:number;duplicate_dimension_records:number;ambiguous_daily_records:number;definition:string;limitations:string[];
 monthly:{site:string;metric:string;unit:string;month:string;calendar_days:number;valid_days:number;mean:Nullable;min:Nullable;max:Nullable;coverage_pct:number}[];
 coverage:{site:string;metric:string;unit:string;record_days:number;valid_days:number;missing_or_absent_days:number;missing_pct:number;annual_observed_mean:Nullable;minimum:Nullable;maximum:Nullable}[];
}
export interface Model {available:boolean;reason?:string;target:string;selected:string;train_n:number;daegu_n:number;excluded_n:number;importance_n:number;validation:string;limitation:string;evaluations:{name:string;cv:Score;daegu:Score|null}[];predictions:Prediction[];importance:{feature:string;mean:number;std:number}[];features:{key:string;label:string}[];shap?:ShapAnalysis;}
export interface Analysis {
 meta:{year:number;previous_year:number;verified_on:string;source_url:string;statistics_url:string;volume_definition:string;mass_definition:string;peer_definition:string;limitations:string[];factor:{value:number;unit:string;approval_year:number;statistics_period:string;boundary:string;source_url:string;note:string}};
 summary:{daegu:Summary;national:Summary}; facilities:Facility[]; national:Facility[]; peers:Record<string,Peer>;
 scale_comparison:{scale:string;national_n:number;daegu_n:number;national_median:Nullable;daegu_median:Nullable}[];
 method_comparison:{method:string;n:number;median:number;q25:number;q75:number;median_bod_removal:number}[];
 correlations:Record<string,Record<string,number>>;
 trends:{facility_id:string;name:string;previous_year:number;year:number;electricity_previous:Nullable;electricity_current:Nullable;intensity_previous:Nullable;intensity_current:Nullable;energy_change_pct:Nullable}[];
 model:Model; quality:{rows:number;column_count:number;encoding:string;flagged_n:number;benchmark_n:number;daegu_benchmark_n:number;coordinates_n:number;coordinates_verified_n:number;coordinates_estimated_n:number;flags:Record<string,number>;columns:{original:string;standard:string|null;unit:string;missing_n:number;missing_pct:number;parse_failure_n:Nullable}[];year_verification:{status:string;rows:number;columns:Record<string,{matched:number;total:number}>};previous_year_note:string;};
 coordinates:MapCoordinate[];
 supplementary:{year:number;sludge:{generated_t_year:number;treated_t_year:number};reuse:{annual_treated_thousand_t:number;reused_thousand_t_year:number;reuse_pct:number}};
 insights:Insight[];
 operational_api?:OperationalAPI;
}
