#================================匯入函數===============================
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report,roc_curve, roc_auc_score
from xgboost import XGBClassifier
import matplotlib.pyplot as plt
import seaborn as sns
import shap
import os
#======================================================================

df = pd.read_csv("D:/AI_prediction/python_program/program1/new_all_teams_data.csv", encoding="utf-8-sig")
df = np.round(df, 3) # 改變資料只到小數第三位

X = df.drop(columns=["result"], axis=1)  # 特徵欄位，axis=1(欄位)刪掉result欄位。
y = df["result"]                 # 標籤欄位

#================================分割資料為訓練集和測試集===============================
# stratify=y按照y的分布來切分資料，保持訓練和測試資料的勝負比例相同。
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
) 
#===================================================================================

#================================建立模型===============================
xgb_model = XGBClassifier(
    objective='binary:logistic',  # 二元分類
    eval_metric='logloss',        # 損失函數
    n_estimators=100,             # 樹的數量
    max_depth=5,                  # 樹深度(層數)
    learning_rate=0.1,            # 學習率
    random_state=42
)
#======================================================================

#================================訓練模型===============================
xgb_model.fit(X_train, y_train)
#======================================================================

#================================印出資訊======================================
# 預測
y_pred = xgb_model.predict(X_test)

# 準確率
acc = accuracy_score(y_test, y_pred)
print("Accuracy:", acc)

# 混淆矩陣
cm = confusion_matrix(y_test, y_pred) # 計算混淆矩陣
print("Confusion Matrix:\n", cm)

# 詳細分類報告
print(classification_report(y_test, y_pred, digits=4))
#=============================================================================

#================================5-fold cross-validation======================
scores = cross_val_score(xgb_model, X, y, cv=5, scoring='accuracy')
print("每一 fold 的準確率:", scores)
print("平均準確率:", np.mean(scores))
#=============================================================================

#================================混淆矩陣圖======================
plt.figure(figsize=(6,4)) # 寬6吋 、 高4吋
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues") # sns.heatmap()畫熱力圖用 、 annot=True(每個格子中是否顯示數據) 、 fmt="d"(格子中的數字顯示整數) 、 cmap="Blues"(顯示圖為藍色主題)
plt.title("Confusion Matrix")
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.tight_layout()
plt.savefig(("XGBoost_image/confusion_matrix.png"), dpi=150)
plt.close()
print("Confusion matrix saved as confusion_matrix.png\n")
#==============================================================

#===========================5-fold 準確率圖==================
plt.figure(figsize=(6,4))
plt.bar(range(1,6), scores) #plt.bar()畫長條圖用 、 range(1,6)這個是X軸座標 、 scores這個是y軸座標(5次的準確率)
plt.title("5-Fold Cross-Validation Accuracy")
plt.xlabel("Fold")
plt.ylabel("Accuracy")
plt.ylim(0,1)      # 設定 y 軸的範圍（上下限）
plt.tight_layout() # 自動調整圖表的空間配置
plt.savefig("XGBoost_image/cross_val_accuracy.png", dpi=150)
plt.close()
print("Cross-validation plot saved as cross_val_accuracy.png\n")
#=========================================================

#==================================ROC Curve圖=====================================
y_prob = xgb_model.predict_proba(X_test)[:, 1] # y_prob模型預測贏的機率

fpr, tpr, thresholds = roc_curve(y_test, y_prob)
auc = roc_auc_score(y_test, y_prob)

plt.figure(figsize=(6,5))
plt.plot(fpr, tpr, label=f"XGBoost (AUC = {auc:.4f})")
plt.plot([0,1], [0,1], 'k--', label="Random")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve")
plt.legend() # 顯示圖例
plt.tight_layout() # 自動調整圖表的空間配置
plt.savefig("XGBoost_image/ROC_curve.png", dpi=150)
plt.close()
print("ROC_curve plot saved as ROC_curve.png\n")
#==============================================================================

#==================================特徵重要度圖=====================================
importance = xgb_model.feature_importances_ # 取得每個特徵的重要度分數（0~1之間）
features = X.columns # 取得特徵名稱

# 排序後畫圖
indices = np.argsort(importance)[::-1]

plt.figure(figsize=(10,6))
plt.bar(range(len(features)), importance[indices]) # range(len(features))特徵數量 、 importance[indices]按照排序後的重要度索引取出數值畫出長條圖。
plt.xticks(range(len(features)), features[indices], rotation=90) # range(len(features))特徵數量 、 features[indices]由特徵權重大到小排序到X軸(特徵名稱) 、 rotation=90把文字旋轉 90 度（直立顯示）
plt.title("XGBoost Feature Importance")
plt.tight_layout()
plt.savefig("XGBoost_image/Feature_importance.png", dpi=150)
plt.close()
print("Feature_importance plot saved as Feature_importance.png\n")
#=================================================================================

#==================================SHAP解釋=====================================
explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(X_test)

# ----------------------------
# 1. 全域特徵重要度 (bar plot)。 Bar plot 是 取平均絕對值，所以只顯示「影響力大小」，不會顯示增加或降低勝率。
#假設特徵 𝑗 的 5 個樣本 SHAP 值如下：
#ϕj​=[0.2,−0.3,0.1,−0.1,0.5] 相同特徵的SHAP值，∣0.2∣ − ∣0.3∣ + ∣0.1∣ − ∣0.1∣ + ∣0.5∣​ / 5 = 0.08
# ----------------------------
plt.figure()
shap.summary_plot(shap_values, X_test, plot_type="bar", show=False)  # show=False 不直接顯示
plt.savefig("XGBoost_image/shap_summary_bar.png", dpi=150, bbox_inches='tight')     # 存成 PNG
plt.close()  # 釋放圖形資源
print("shap_summary_bar plot saved as shap_summary_bar.png\n")

# ----------------------------
# 2. 詳細 SHAP 分佈 (dot plot)
# ----------------------------
plt.figure()
shap.summary_plot(shap_values, X_test, show=False)
plt.savefig("XGBoost_image/shap_summary_dot.png", dpi=150, bbox_inches='tight')
plt.close()  # 釋放圖形資源
print("shap_summary_dot plot saved as shap_summary_dot.png\n")
#===============================================================================