#!/usr/bin/env python3
import time
from typing import Callable
# Array has n = 9 elemtents 
array =  [-5, 3, 2, 7, 1, 4, -10, 3, 6]
positive_array =  [5, 3, 2, 7, 1, 4, 10, 3, 6]
answer = [-10, -5, 1, 2, 3, 3, 4, 6, 7]

# Bubble Sort
def bubble_sort(arr):
    length = len(arr)
    swap = True
    while swap:
        swap = False
        for i in range(length):
            if i + 1 >= length:
                continue
            if arr[i + 1] < arr[i]:
                arr[i], arr[i+1] = arr[i+1], arr[i]
                swap = True
    return arr

# Insertion Sort
def insertion_sort(arr):
    length = len(arr)
    for i in range(1, length):
        for j in range(i, 0, -1):
            if arr[j - 1] > arr[j]:
                arr[j - 1], arr[j] = arr[j], arr[j - 1]
            else:
                break
    return arr

# Selection Sort
def selection_sort(arr):
    length = len(arr)
    for i in range(length):
        m = i
        for j in range(i + 1, length):
            if arr[m] > arr[j]:
                m = j
        if arr[i] > arr[m]:
            arr[i], arr[m] = arr[m], arr[i]
        # arr[i], arr[m] = arr[m], arr[i]
    return arr
                
# Merge Sort
def merge_sort(arr):
    n = len(arr)

    if n == 1:
        return arr

    midpoint = n // 2
    left = arr[:midpoint]
    right = arr[midpoint:]
    L = merge_sort(left)
    R = merge_sort(right)

    len_l = len(L)
    len_r = len(R)
    l = 0
    r = 0
    sorted_array = [0] * n
    i = 0

    while l < len_l and r < len_r:
        if L[l] < R[r]:
            sorted_array[i] = L[l]
            l += 1
        else:
            sorted_array[i] = R[r]
            r += 1
        i += 1

    while l < len_l:
        sorted_array[i] = L[l]
        l += 1
        i += 1

    while r < len_r:
        sorted_array[i] = R[r]
        r += 1
        i += 1

    return sorted_array

# My Quick Sort Implementation
def my_quick_sort(arr):
    n = len(arr)

    if n <= 1:
        return arr  # base

    pivot = arr[-1]
    comp_arr = my_quick_sort(arr[:-1])

    less = []
    greater = []
    for num in comp_arr:
        if num <= pivot:
            less.append(num)
        else:
            greater.append(num)
    return less + [pivot] + greater

def quick_sort(arr):
    
    if len(arr) <= 1:
        return arr

    pivot = arr[-1]
    less = [x for x in arr[:-1] if x <= pivot]
    right = [x for x in arr[:-1] if x > pivot]

    less = quick_sort(less)
    right = quick_sort(right)

    return less + [pivot] + right

def my_count_sort(arr):
    n = len(arr)
    k = max(arr)
    # This implementation assumes only positive values
    if min(arr) < 0:
        return None
    count_arr = [0] * (k + 1)  # Length k + 1 array

    for i in arr:
        count_arr[i] += 1

    c = 0
    for i in range(n):
        while count_arr[c] == 0:
            c += 1
        arr[i] = c
        count_arr[c] -= 1
    #return arr  # initial but editted out since arr was editted directly
    
def count_sort(arr):
    n = len(arr)
    k = max(arr)
    # This implementation assumes only positive values
    if min(arr) < 0:
        return None
    count_arr = [0] * (k + 1)  # Length k + 1 array

    for i in arr:
        count_arr[i] += 1

    i = 0
    for c in range(k + 1):
        while count_arr[c] > 0:
            arr[i] = c
            count_arr[c] -= 1
            i += 1

# Exercise run a generic count sort alg that works for all intergers!
def general_count_sort(arr):
    pass

def compare(name: str, arr: list, expected: list, alg: Callable, copy: bool = False):
    # Name of alg, Output of alg, Whether it was correct, Time alg took
    output_format = "[Using compare()] {}: {}\n\tCorrect: {}\n\tTime: {}"
    # Copy list and set output to compare
    if copy:
        arr = arr.copy()
        before = time.time()
        alg(arr)
        after = time.time()
        output = arr
    else:
        before = time.time()
        output = alg(arr)
        after = time.time()
    time_took = after - before
    correct = expected == output
    print(output_format.format(name, output, correct, time_took))

print(f"Array: {array}")
print(f"Answer: {answer}")

compare("Bubble Sort", array, answer, bubble_sort)

before = time.time()
bubble_sorted_arr = bubble_sort(array)
after = time.time()
print(f"Bubble sort: {bubble_sorted_arr}\n\tCorrect: {answer == bubble_sorted_arr}\n\tTime: {after - before}")

compare("Insertion Sort", array, answer, insertion_sort)

before = time.time()
insertion_sorted_arr = insertion_sort(array)
after = time.time()
print(f"Insertion sort: {insertion_sorted_arr}\n\tCorrect: {answer == insertion_sorted_arr}\n\tTime: {after - before}")

compare("Selection Sort", array, answer, selection_sort)

before = time.time()
selection_sorted_arr = selection_sort(array)
after = time.time()
print(f"Selection sort: {selection_sorted_arr}\n\tCorrect: {answer == selection_sorted_arr}\n\tTime: {after - before}")

compare("Merge Sort", array, answer, merge_sort)

before = time.time()
merge_sorted_arr = merge_sort(array)
after = time.time()
print(f"Merge sort: {merge_sorted_arr}\n\tCorrect: {answer == merge_sorted_arr}\n\tTime: {after - before}")

compare("My Quick Sort", array, answer, my_quick_sort)

before = time.time()
my_quick_sorted_arr = my_quick_sort(array)
after = time.time()
print(f"My Quick sort: {my_quick_sorted_arr}\n\tCorrect: {answer == my_quick_sorted_arr}\n\tTime: {after - before}")

compare("Quick Sort", array, answer, quick_sort)

before = time.time()
quick_sorted_arr = quick_sort(array)
after = time.time()
print(f"Quick sort: {quick_sorted_arr}\n\tCorrect: {answer == quick_sorted_arr}\n\tTime: {after - before}")


print(f"------------\nPositive Array for Counting Sorts: {positive_array}\n")
pos_answer = [1, 2, 3, 3, 4, 5, 6, 7, 10]

compare("My Count Sort", positive_array, pos_answer, my_count_sort, copy = True)

copy = positive_array.copy()
before = time.time()
my_count_sort(copy)
after = time.time()
print(f"My Count sort: {copy}\n\tCorrect: {pos_answer == copy}\n\tTime: {after - before}")


compare("Count Sort", positive_array, pos_answer, count_sort, copy = True)

copy = positive_array.copy()
before = time.time()
count_sort(copy)
after = time.time()
print(f"Count sort: {copy}\n\tCorrect: {pos_answer == copy}\n\tTime: {after - before}")

