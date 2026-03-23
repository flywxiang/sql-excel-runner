	-- 正式版、检查版

	SELECT
		st.key_id,
		st.real_add_time,
	CASE
		
		WHEN st.tenant_category = 0 THEN
		'正式版' 
		WHEN st.tenant_category = 1 THEN
		'检查版' 
		WHEN st.tenant_category = 2 THEN
		'互联网版' 
		END AS tenant_category,
	CASE
			
			WHEN NAME LIKE '%口腔%' THEN
			'口腔诊所' 
			WHEN NAME LIKE '%中医%' THEN
			'中医诊所' ELSE '中西医诊所' -- 或者你可以设置为其他默认值，比如 -1
			
		END AS type,
		CONCAT( st.province, '', st.city ),
		st.county,
		st.NAME,
		st.address,									-- 地 址
		st.last_log_time,						-- 最近一次登录时间
		t1.latest_pay,							-- 最近一次交易时间
		t.latest_case_create,				-- 最近一次处方创建时间
		t2.latest_commodity_add,		-- 最近一次药品更新时间
		t3.latest_inv_op,						-- 最近一次库存操作时间
		t4.total_paid_price_week,		-- 近一周交易额
		t5.total_paid_price_month,	-- 近一个月交易额
		t6.total_paid_price_tmonth,	-- 近三个月交易额
		t7.total_paid_price,				-- 今年内交易额
		t4.total_paid_num_week,			-- 近一周交易笔数
		t5.total_paid_num_month,		-- 近一个月交易笔数
		t6.total_paid_num_tmonth,		-- 近三个月交易笔数
		t7.total_paid_num,					-- 今年内交易笔数
		t8.average_order_value , 		-- 客单价
		(t5.total_paid_price_month -  t9.total_paid_price_tm) / t9.total_paid_price_tm,    -- 交易额增长率(近一个月)
		(t9.total_paid_price_tm -  t10.total_paid_price_t2m) / t10.total_paid_price_t2m,   -- 交易额增长率(近两个月)
		(t10.total_paid_price_t2m -  t11.total_paid_price_t3m) / t11.total_paid_price_t3m  -- 交易额增长率(近三个月)
	FROM
		sys_tenant st
		LEFT JOIN ( -- 最近支付时间
		SELECT
			np.tenant_id,
			MAX( np.real_modify_time ) AS latest_pay 
		FROM
			(select * from npm_bill_1_2026 union all select * from npm_bill_4_2026 union all select * from npm_bill_3_2026 union all select * from npm_bill_1_2025 union all select * from npm_bill_4_2025 union all select * from npm_bill_3_2025
			) np
		WHERE 
			np.bill_state_code = 10 
			AND np.del_status = 0 
		GROUP BY
			np.tenant_id 
		) t1 ON t1.tenant_id = st.key_id
		LEFT JOIN ( -- 最近一次处方创建时间
		SELECT
			np.tenant_id,
			MAX( np.real_add_time ) AS latest_case_create
		FROM
			(select * from npm_case_history_1_2026 union all select * from npm_case_history_4_2026 union all select * from npm_case_history_3_2026 union all select * from npm_case_history_1_2025 union all select * from npm_case_history_4_2025 union all select * from npm_case_history_3_2025
			) np
		WHERE 
			np.del_status = 0 
		GROUP BY
			np.tenant_id 
		) t ON t.tenant_id = st.key_id
		LEFT JOIN ( -- 商品最近添加时间
		SELECT
			noc.tenant_id,
			MAX( noc.add_time ) AS latest_commodity_add 
		FROM
			(select * from npm_org_commodity_1 union all select * from npm_org_commodity_4 union all select * from npm_org_commodity_3) noc 
		WHERE
			noc.del_status = 0 
			and drug_type_code not in (15,16)
		GROUP BY
			noc.tenant_id 
		) t2 ON t2.tenant_id = st.key_id
		LEFT JOIN ( -- 库存最近操作时间
		SELECT
			nir.tenant_id,
			MAX( nir.add_time ) AS latest_inv_op 
		FROM
				(select * from npm_inventory_resume_1_2026 union all select * from npm_inventory_resume_4_2026 union all select * from npm_inventory_resume_3_2026 union all select * from npm_inventory_resume_1_2025 union all select * from npm_inventory_resume_4_2025 union all select * from npm_inventory_resume_3_2025
				) nir
		WHERE
			nir.del_status = 0 
		GROUP BY
			nir.tenant_id 
		) t3 ON t3.tenant_id = st.key_id
		LEFT JOIN ( -- 近一周
		SELECT 
			nb.tenant_id,
			SUM( nb.paid_price ) AS total_paid_price_week,
			COUNT( 1 ) AS total_paid_num_week 
		FROM
			(select * from npm_bill_1_2026 union all select * from npm_bill_4_2026 union all select * from npm_bill_3_2026 union all select * from npm_bill_1_2025 union all select * from npm_bill_4_2025 union all select * from npm_bill_3_2025
			) nb
		WHERE
			nb.del_status = 0 
			AND nb.bill_state_code = 10 
			AND nb.charge_time >= '2026-03-23' - INTERVAL 1 WEEK 
			AND nb.charge_time < '2026-03-23' 
		GROUP BY
			nb.tenant_id 
		) t4 ON t4.tenant_id = st.key_id
		LEFT JOIN ( -- 近一个月
		SELECT
			nb.tenant_id,
			SUM( nb.paid_price ) AS total_paid_price_month,
			COUNT( 1 ) AS total_paid_num_month 
		FROM
			(select * from npm_bill_1_2026 union all select * from npm_bill_4_2026 union all select * from npm_bill_3_2026 union all select * from npm_bill_1_2025 union all select * from npm_bill_4_2025 union all select * from npm_bill_3_2025
			) nb
		WHERE
			nb.del_status = 0 
			AND nb.bill_state_code = 10 
			AND nb.charge_time >= '2026-03-23' - INTERVAL 1 MONTH 
			AND nb.charge_time < '2026-03-23' -- 	AND nb.tenant_id
			
		GROUP BY
			nb.tenant_id 
		) t5 ON t5.tenant_id = st.key_id
		LEFT JOIN ( -- 近三个月
		SELECT
			nb.tenant_id,
			SUM( nb.paid_price ) AS total_paid_price_tmonth,
			COUNT( 1 ) AS total_paid_num_tmonth 
		FROM
			(select * from npm_bill_1_2026 union all select * from npm_bill_4_2026 union all select * from npm_bill_3_2026 union all select * from npm_bill_1_2025 union all select * from npm_bill_4_2025 union all select * from npm_bill_3_2025
			) nb
		WHERE
			nb.del_status = 0 
			AND nb.bill_state_code = 10 
			AND nb.charge_time >= '2026-03-23' - INTERVAL 3 MONTH 
			AND nb.charge_time < '2026-03-23' -- 	AND nb.tenant_id
			
		GROUP BY
			nb.tenant_id 
		) t6 ON t6.tenant_id = st.key_id
		LEFT JOIN ( -- 今年内
		SELECT
			nb.tenant_id,
			sum( nb.paid_price ) AS total_paid_price,
			count( 1 ) AS total_paid_num 
		FROM
			(select * from npm_bill_1_2026 union all select * from npm_bill_4_2026 union all select * from npm_bill_3_2026 union all select * from npm_bill_1_2025 union all select * from npm_bill_4_2025 union all select * from npm_bill_3_2025
			) nb
		WHERE
			nb.del_status = 0 
			AND nb.bill_state_code = 10 
			AND YEAR ( nb.charge_time ) = YEAR ( '2026-03-23' ) 
		GROUP BY
			nb.tenant_id 
		) t7 ON t7.tenant_id = st.key_id
		LEFT JOIN (-- 客单价
		SELECT
			nor.tenant_id,
			SUM( nor.paid_price ) / COUNT( DISTINCT nor.patient_id ) AS average_order_value 
		FROM
			(select * from npm_order_1_2026 union all select * from npm_order_4_2026 union all select * from npm_order_3_2026 union all select * from npm_order_1_2025 union all select * from npm_order_4_2025 union all select * from npm_order_3_2025
			) nor
		WHERE
			nor.del_status = 0 
			AND nor.order_status_code = 30 
			AND YEAR ( nor.creat_time ) = YEAR ( '2026-03-23' ) 
		GROUP BY
			nor.tenant_id 
		) t8 ON t8.tenant_id = st.key_id 
		LEFT JOIN ( -- 近2个月到近1个月的数据
			SELECT
		nb.tenant_id,
	-- 	add_time
		sum( nb.paid_price ) AS total_paid_price_tm,
		count( 1 ) AS total_paid_num_tm
	FROM
		(select * from npm_bill_1_2026 union all select * from npm_bill_4_2026 union all select * from npm_bill_3_2026 union all select * from npm_bill_1_2025 union all select * from npm_bill_4_2025 union all select * from npm_bill_3_2025
			) nb
	WHERE
		nb.del_status = 0 
		AND nb.bill_state_code = 10 
		AND nb.charge_time >= '2026-03-23' - INTERVAL 2 MONTH 
				AND nb.charge_time < '2026-03-23'- INTERVAL 1 MONTH  -- 	AND nb.tenant_id
	GROUP BY
		nb.tenant_id
		) t9 on st.key_id=t9.tenant_id
		LEFT JOIN ( -- 近3个月到近2个月的数据
			SELECT
		nb.tenant_id,
	-- 	add_time
		sum( nb.paid_price ) AS total_paid_price_t2m,
		count( 1 ) AS total_paid_num_t2m
	FROM
		(select * from npm_bill_1_2026 union all select * from npm_bill_4_2026 union all select * from npm_bill_3_2026 union all select * from npm_bill_1_2025 union all select * from npm_bill_4_2025 union all select * from npm_bill_3_2025
			) nb
	WHERE
		nb.del_status = 0 
		AND nb.bill_state_code = 10 
		AND nb.charge_time >= '2026-03-23' - INTERVAL 3 MONTH 
				AND nb.charge_time < '2026-03-23'- INTERVAL 2 MONTH  -- 	AND nb.tenant_id
	GROUP BY
		nb.tenant_id
		) t10 on st.key_id=t10.tenant_id
		LEFT JOIN ( -- 近3个月到近2个月的数据
			SELECT
		nb.tenant_id,
	-- 	add_time
		sum( nb.paid_price ) AS total_paid_price_t3m,
		count( 1 ) AS total_paid_num_t3m
	FROM
		(select * from npm_bill_1_2026 union all select * from npm_bill_4_2026 union all select * from npm_bill_3_2026 union all select * from npm_bill_1_2025 union all select * from npm_bill_4_2025 union all select * from npm_bill_3_2025 
			) nb
	WHERE
		nb.del_status = 0 
		AND nb.bill_state_code = 10 
		AND nb.charge_time >= '2026-03-23' - INTERVAL 4 MONTH 
				AND nb.charge_time < '2026-03-23'- INTERVAL 3 MONTH  -- 	AND nb.tenant_id
	GROUP BY
		nb.tenant_id
		) t11 on st.key_id=t11.tenant_id
	WHERE
		st.is_test = 0 
		and st.enable=1
		AND st.del_status = 0 
		-- AND st.tenant_category IN ( 0, 1 ) 
		-- order by st.add_time

