-- Seed: 30 sample insurance plans (run after schema.sql)
-- Demo data for the recommender. Premiums and features are illustrative, not real quotes.

USE valuetrack;

INSERT INTO insurance
  (plan_name, plan_type, min_age, max_age, coverage_amount,
   has_critical_illness, has_maternity, has_accident, co_pay_percentage, monthly_premium)
VALUES
  ('Star Comprehensive'      , 'Family Floater', 18, 65,    500000.00, 1, 1, 1,  0,   710.00),
  ('Star Young Plan'         , 'Young Adult'   , 18, 35,    300000.00, 0, 0, 1,  0,   420.00),
  ('Optima Secure'           , 'Comprehensive' , 21, 60,   1000000.00, 1, 1, 1,  0,  1000.00),
  ('Optima Restore'          , 'Family Floater', 25, 55,   1500000.00, 1, 1, 1,  0,  1250.00),
  ('iHealth Plan'            , 'Individual'    , 18, 50,    400000.00, 0, 0, 1, 10,   500.00),
  ('Complete Health'         , 'Comprehensive' , 20, 65,    750000.00, 1, 1, 0,  0,   920.00),
  ('Health Guard'            , 'Individual'    , 18, 70,    500000.00, 1, 0, 1, 10,   790.00),
  ('Health Prime'            , 'Comprehensive' , 22, 55,   2000000.00, 1, 1, 1,  0,  1500.00),
  ('GoActive'                , 'Young Adult'   , 18, 45,    200000.00, 0, 0, 1,  0,   380.00),
  ('Health Companion'        , 'Family Floater', 25, 60,    600000.00, 0, 1, 1,  0,   830.00),
  ('Mediclaim Policy'        , 'Individual'    , 18, 65,    300000.00, 0, 0, 0, 10,   580.00),
  ('Senior Mediclaim'        , 'Senior Citizen', 60, 80,    500000.00, 1, 0, 1, 20,  1670.00),
  ('Medicare'                , 'Individual'    , 18, 65,    400000.00, 0, 0, 1, 10,   670.00),
  ('Medicare Premier'        , 'Comprehensive' , 20, 55,   1000000.00, 1, 1, 1,  0,  1170.00),
  ('ReAssure 2.0'            , 'Family Floater', 18, 65,    500000.00, 1, 1, 0,  0,   750.00),
  ('Care Supreme'            , 'Comprehensive' , 18, 65,   1000000.00, 1, 1, 1,  0,   960.00),
  ('Care Advantage'          , 'Individual'    , 18, 70,    500000.00, 1, 0, 1, 10,   770.00),
  ('Activ Health Platinum'   , 'Comprehensive' , 18, 65,   1000000.00, 1, 1, 1,  0,  1080.00),
  ('Activ Assure Diamond'    , 'Family Floater', 18, 60,    750000.00, 1, 1, 0,  0,   820.00),
  ('Arogya Supreme'          , 'Comprehensive' , 18, 65,   1000000.00, 1, 1, 1,  0,   880.00),
  ('Arogya Plus'             , 'Individual'    , 18, 60,    500000.00, 0, 0, 1,  0,   600.00),
  ('Health Infinity'         , 'Individual'    , 18, 65,    500000.00, 1, 0, 1, 10,   730.00),
  ('Health Gain'             , 'Young Adult'   , 18, 60,    400000.00, 0, 0, 1,  0,   540.00),
  ('Health Total'            , 'Family Floater', 18, 65,    750000.00, 1, 1, 1,  0,   830.00),
  ('Health Absolute'         , 'Individual'    , 18, 60,    500000.00, 0, 1, 0,  0,   670.00),
  ('Healthline Insurance'    , 'Individual'    , 18, 65,    500000.00, 0, 0, 1, 10,   650.00),
  ('Family Healthline'       , 'Family Floater', 18, 65,    750000.00, 0, 1, 1,  0,   720.00),
  ('Kotak Health Premier'    , 'Comprehensive' , 18, 65,   1000000.00, 1, 1, 1,  0,   850.00),
  ('Kotak Health Care'       , 'Individual'    , 18, 60,    500000.00, 0, 0, 1,  0,   660.00),
  ('Lifeline Elite'          , 'Senior Citizen', 50, 80,   1000000.00, 1, 0, 1, 20,  1450.00);
