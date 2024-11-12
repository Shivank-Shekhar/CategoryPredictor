# import pickle
# import pandas as pd
# new_df=pd.read_csv('homeroots.csv')
#
# new_df.head()
#
# new_df.rename(columns={"Category Name": "category"}, inplace=True)
# new_df.rename(columns={"Title": "title"}, inplace=True)
#
# new_df.head()
#
# from sklearn.model_selection import train_test_split
# from sklearn.feature_extraction.text import CountVectorizer
# from sklearn.metrics import accuracy_score
#
#
# # Handle missing values
# new_df = new_df.dropna(subset=['category', 'title'])
#
# # Split the data into training and testing sets
# train_data, test_data = train_test_split(new_df, test_size=0.2, random_state=42)
#
# # Vectorize the titles using CountVectorizer
# vectorizer = CountVectorizer()
# X_train = vectorizer.fit_transform(train_data['title'])
# X_test = vectorizer.transform(test_data['title'])
#
#
# from sklearn.ensemble import RandomForestClassifier
# model =RandomForestClassifier(n_estimators=100, random_state=42)
#
# model.fit(X_train, train_data['category'])
#
# pickle.dump(model,open('mdl.pkl','wb'))
#
# # Make predictions on the test set
# predictions = model.predict(X_test)
#
# # Calculate accuracy
# accuracy = accuracy_score(test_data['category'], predictions)
# print(f"Accuracy of RF: {accuracy * 100:.2f}%")
#


from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pandas as pd
import pickle

# Load the data
new_df = pd.read_csv('homeroots.csv')

# Rename columns
new_df.rename(columns={"Category Name": "category", "Title": "title"}, inplace=True)

# Handle missing values
new_df = new_df.dropna(subset=['category', 'title'])

# Split the data into training and testing sets
train_data, test_data = train_test_split(new_df, test_size=0.2, random_state=42)

# Vectorize the titles using CountVectorizer
vectorizer = CountVectorizer()
X_train = vectorizer.fit_transform(train_data['title'])
X_test = vectorizer.transform(test_data['title'])

# Train the model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, train_data['category'])

# Save the model and the vectorizer
with open('mdl.pkl', 'wb') as model_file:
    pickle.dump(model, model_file)

with open('vectorizer.pkl', 'wb') as vectorizer_file:
    pickle.dump(vectorizer, vectorizer_file)

# Make predictions on the test set
predictions = model.predict(X_test)

# Calculate accuracy
accuracy = accuracy_score(test_data['category'], predictions)
print(f"Accuracy of RF: {accuracy * 100:.2f}%")
