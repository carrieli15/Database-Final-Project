\COPY Users FROM 'Users.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.users_user_id_seq', (SELECT MAX(user_id)+1 FROM Users), false);

\COPY Sellers FROM 'Sellers.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.sellers_seller_id_seq', (SELECT MAX(seller_id)+1 FROM Sellers), false);

\COPY Accounts FROM 'Accounts.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.accounts_account_id_seq', (SELECT MAX(account_id)+1 FROM Accounts), false);

\COPY Products FROM 'Products.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.products_product_id_seq', (SELECT MAX(product_id)+1 FROM Products), false);

\COPY Categories FROM 'Categories.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.categories_category_id_seq', (SELECT MAX(category_id)+1 FROM Categories), false);

\COPY Product_reviews FROM 'Product_reviews.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.product_reviews_product_review_id_seq', (SELECT MAX(product_review_id)+1 FROM Product_reviews), false);

\COPY Purchases FROM 'Purchases.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.purchases_purchase_id_seq', (SELECT MAX(purchase_id)+1 FROM Purchases), false);

\COPY Purchase_items FROM 'Purchase_items.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.purchase_items_purchase_item_id_seq', (SELECT MAX(purchase_item_id)+1 FROM Purchase_items), false);

\COPY Seller_purchases FROM 'Seller_purchases.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.seller_purchases_seller_purchase_id_seq', (SELECT MAX(seller_purchase_id)+1 FROM Seller_purchases), false);

\COPY Seller_purchase_items FROM 'Seller_purchase_items.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.seller_purchase_items_seller_purchase_item_id_seq', (SELECT MAX(seller_purchase_item_id)+1 FROM Seller_purchase_items), false);

\COPY Inventory FROM 'Inventory.csv' WITH DELIMITER ',' NULL '' CSV
--SELECT pg_catalog.setval('public.inventory_item_id_seq', (SELECT MAX(item_id)+1 FROM Inventory), false); 

--\COPY Inventory (item_id, seller_id, product_id, price, quantity, created_at, publish_status, low_stock_quantity)
--FROM 'Inventory.csv' WITH DELIMITER ',' NULL '' CSV; # jiechen updated

SELECT pg_catalog.setval('public.inventory_item_id_seq', COALESCE((SELECT MAX(item_id)+1 FROM Inventory), 1), false);
 --# jiechen updated

\COPY Cart FROM 'Cart.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.cart_cart_id_seq', (SELECT MAX(cart_id)+1 FROM Cart), false);

\COPY Cart_items FROM 'Cart_items.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.cart_items_cart_item_id_seq', (SELECT MAX(cart_item_id)+1 FROM Cart_items), false);

\COPY Seller_reviews FROM 'Seller_reviews.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.seller_reviews_seller_review_id_seq', (SELECT MAX(seller_review_id)+1 FROM Seller_reviews), false);

\COPY Account_transactions FROM 'Account_transactions.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.account_transactions_account_transaction_id_seq', (SELECT MAX(account_transaction_id)+1 FROM Account_transactions), false);

\COPY Coupons FROM 'Coupons.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.coupons_coupon_id_seq', (SELECT MAX(coupon_id)+1 FROM Coupons), false);


-- UPDATED based on latest schema



/* \COPY Users FROM 'Users.csv' WITH DELIMITER ',' NULL '' CSV
-- since id is auto-generated; we need the next command to adjust the counter
-- for auto-generation so next INSERT will not clash with ids loaded above:
SELECT pg_catalog.setval('public.users_id_seq',
                         (SELECT MAX(id)+1 FROM Users),
                         false);

\COPY Products FROM 'Products.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.products_id_seq',
                         (SELECT MAX(id)+1 FROM Products),
                         false);

\COPY Purchases FROM 'Purchases.csv' WITH DELIMITER ',' NULL '' CSV
SELECT pg_catalog.setval('public.purchases_id_seq',
                         (SELECT MAX(id)+1 FROM Purchases),
                         false); */
